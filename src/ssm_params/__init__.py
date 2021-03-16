from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import anytree
from mypy_boto3_ssm import Client


__version__ = "2021.2.1"
# TODO: 2021-02-09
# - refresh all
# - refresh at path or leaf
# - auto-fetch from Secrets Manager if leaf.value is an ARN


def get_nested_dict(*, client: Client, path: str, strip_root: bool = True) -> Dict[str, Any]:
    paginator = client.get_paginator("get_parameters_by_path")
    page_iterator = paginator.paginate(Path=path, Recursive=True, WithDecryption=True)
    config = {}
    if strip_root:
        root = len(path) + 1  # Remove root path and leading slash.
    else:
        root = 1  # Remove just the leading slash.
    for page in page_iterator:
        for parameter in page["Parameters"]:
            path = parameter["Name"][root:].split("/")
            base = config
            for part in path[:-1]:
                if part not in base:
                    base[part] = {}
                base = base[part]
            base[path[-1]] = parameter["Value"]
    return config


class ConfigNode(anytree.NodeMixin):
    def __init__(
        self,
        name: str,
        value: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        parent: ConfigNode = None,
        children: List[ConfigNode] = None,
        client: Client = None,
    ):
        super().__init__()
        self.name = name
        self.value = value
        if meta is None:
            meta = {}
        self.meta = meta
        self.parent = parent
        self.client = client
        if children:  # set children only if given
            self.children = children

    def __repr__(self) -> str:
        if self.is_root:
            rep = f"{self.__class__.__module__}.ConfigRoot({self.name})"
        elif self.is_leaf:
            rep = f"{self.__class__.__module__}.ConfigValue({self.name})"
        else:
            rep = f"{self.__class__.__module__}.ConfigPath({self.name})"
        return rep

    def __str__(self) -> str:
        if self.value is not None:
            return self.value
        else:
            return self.__repr__()

    def __getitem__(self, name: str) -> ConfigNode:
        resolver = anytree.Resolver("name")
        try:
            return resolver.get(self, name)
        except anytree.ChildResolverError:
            raise KeyError(name)

    def __contains__(self, item: Union[str, ConfigNode]) -> bool:
        resolver = anytree.Resolver("name")
        if isinstance(item, self.__class__):
            return item.parent == self
        try:
            resolver.get(self, item)
            return True
        except anytree.ChildResolverError:
            return False

    @property
    def full_path(self) -> str:
        return "/".join([p.name for p in self.path])

    @classmethod
    def create_node_from_parameter(
        cls, *, client: Client, name: str, parameter: Dict[str, Any], parent: Optional[ConfigNode] = None
    ) -> ConfigNode:
        meta = {
            "type": parameter["Type"],
            "arn": parameter["ARN"],
            "version": parameter["Version"],
            "last_modified_date": parameter["LastModifiedDate"],
            "data_type": parameter["DataType"],
        }
        return cls(name=name, value=parameter["Value"], meta=meta, client=client, parent=parent)

    @classmethod
    def create_tree_from_path(cls, *, client: Client, path: str) -> ConfigNode:
        paginator = client.get_paginator("get_parameters_by_path")
        page_iterator = paginator.paginate(Path=path, Recursive=True, WithDecryption=True)
        root = None
        base = None
        for page in page_iterator:
            for parameter in page["Parameters"]:
                path = parameter["Name"].strip("/").split("/")
                # The value of the parameter is only at the leaf node of the full
                # path. We first need to check that all the intermediate paths
                # exists and create them if they don't.
                for part in path[:-1]:
                    if base is None:
                        root = cls(name=part, client=client)
                        base = root
                    else:
                        if part == base.name:
                            continue
                        elif part not in base:
                            base = cls(name=part, client=client, parent=base)
                        else:
                            base = base[part]
                # Now we can create the value at the last leaf of the path.
                cls.create_node_from_parameter(client=client, name=path[-1], parameter=parameter, parent=base)
                base = root
        return root

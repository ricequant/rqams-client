# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。


from collections import OrderedDict
from enum import Enum
from typing import Mapping, Optional, Callable, TypeVar, MutableMapping, Sequence, Any, List
from datetime import date, datetime
from dateutil.parser import parse


__all__ = [
    "DictProxy",
    "DictConvertMixin",
    "property_class"
]


_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


class DictProxy(MutableMapping[_KT, _VT]):
    def __init__(
            self,
            get_func: Optional[Callable[[], Mapping[_KT, _VT]]] = None,
            del_func: Optional[Callable[[_KT, ], Any]] = None,
            set_func: Optional[Callable[[_KT, _VT], Any]] = None,
            update_func: Optional[Callable[[Mapping[_KT, _VT], ], Any]] = None
    ):
        self._get_func = get_func
        self._del_func = del_func
        self._set_func = set_func
        self._update_func = update_func

    def _get(self):
        if not self._get_func:
            raise TypeError(f"{self.__class__.__name__} object dose not support item getting")
        return self._get_func()

    def __getitem__(self, item: _VT):
        return self._get()[item]

    def __len__(self):
        return len(self._get())

    def __iter__(self):
        return iter(self._get())

    def __setitem__(self, key: _KT, value: _VT):
        if self._set_func:
            return self._set_func(key, value)
        if self._update_func:
            return self._update_func({key: value})
        raise TypeError(f"{self.__class__.__name__} object dose not support item assignment")

    def __delitem__(self, key: _KT):
        if not self._del_func:
            raise TypeError(f"{self.__class__.__name__} object dose not support item deletion")
        return self._del_func(key)

    def update(self, __m: Mapping[_KT, _VT], **kwargs: _VT) -> None:
        if self._update_func:
            return self._update_func(__m)
        for k, v in __m.items():
            self[k] = v

    def items(self):
        return self._get().items()

    def values(self):
        return self._get().values()

    def keys(self):
        return self._get().keys()

    def pop(self, k: _KT) -> _VT:
        value = self[k]
        del self[k]
        return value

    def __repr__(self):
        return "{" + ", ".join("{}: {}".format(k, v) for k, v in self.items()) + "}"


DATA_CONTAINER = "__data"
INIT_FUNC_NAME = "__init__"


def _property(name, before_set: Optional[Callable[[object, Any], None]]):
    def fget(self):
        return getattr(self, DATA_CONTAINER)[name]

    def fset(self, value):
        before_set(self, value)
        getattr(self, DATA_CONTAINER)[name] = value

    return property(fget=fget, fset=fset if before_set else None)


def _repr(self):
    return "{}({})".format(
        self.__class__.__name__, ", ".join("{}={}".format(n, getattr(self, n)) for n in self._fields)
    )


def property_class(cls):
    cls._fields = []
    cls._field_types = OrderedDict()

    for name, type_ in cls.__annotations__.items():
        if name.startswith("_"):
            continue
        cls._fields.append(name)
        cls._field_types[name] = type_
        p = _property(name, getattr(cls, f"_before_set__{name}", None))
        setattr(cls, name, p)

    _init_fn_txt = "def {}(self, {}, client=None):\n".format(INIT_FUNC_NAME, ", ".join(n for n in cls._fields))
    _init_fn_txt += "\n".join(" " * 4 + b for b in [
        f"self.{DATA_CONTAINER} = dict()"
    ] + [
        f"self.{DATA_CONTAINER}[\"{n}\"] = {n}" for n in cls._fields
    ] + ["self._client = client"])
    locals_ = {}
    exec(_init_fn_txt, {}, locals_)
    setattr(cls, INIT_FUNC_NAME, locals_[INIT_FUNC_NAME])
    setattr(cls, "__repr__", _repr)
    return cls


class DictConvertMixin:
    _fields = []
    _field_types = {}
    
    def __init__(self, *args, **kwargs):
        super(DictConvertMixin, self).__init__(*args, **kwargs)

    def to_dict(self):
        d = {}
        for f in self._fields:
            value = getattr(self, f)
            if isinstance(value, DictConvertMixin):
                d[f] = value.to_dict()
            elif isinstance(value, List):
                d[f] = [v.to_dict() if isinstance(v, DictConvertMixin) else v for v in value]
            else:
                d[f] = value
        return d

    @classmethod
    def from_dict(cls, d: dict, client=None):
        _kwargs = {}
        for f, type_ in cls._field_types.items():
            if f in d:
                value = d[f]
                if issubclass(type_, DictConvertMixin):
                    _kwargs[f] = type_.from_dict(value, client)
                else:
                    _kwargs[f] = cls._convert(value, type_)
            else:
                _kwargs[f] = None
        _kwargs["client"] = client
        return cls(**_kwargs)

    @classmethod
    def _convert(cls, value, type_: type):
        if issubclass(type_, Sequence):
            try:
                sub_type = type_.__args__[0]
            except Exception:
                return value
            else:
                return [cls._convert(item, sub_type) for item in value]
        elif issubclass(type_, Enum):
            return type_(value)
        elif issubclass(type_, date) and isinstance(value, str):
            return parse(value).date()
        elif issubclass(type_, datetime):
            return parse(value)
        else:
            return value


if __name__ == "__main__":
    from time import sleep

    @property_class
    class Test(DictConvertMixin):
        a: int

    t = Test(1)
    print(t.a)
    print(t.to_dict())
    print(Test.from_dict({"a": 1}))
    sleep(0.1)
    t.a = 2

"""
iso8583_types.core.interfaces.iso_ports のユニットテスト。

Protocol の構造 (メソッドシグネチャ) を検証する。
"""
import inspect
from iso8583_types.core.interfaces.iso_ports import IIso8583Model, IMessageGenerator


class TestIIso8583ModelProtocol:
    def test_has_to_iso_dict_method(self):
        assert hasattr(IIso8583Model, "to_iso_dict")

    def test_has_from_iso_dict_classmethod(self):
        assert hasattr(IIso8583Model, "from_iso_dict")

    def test_to_iso_dict_has_return_annotation(self):
        sig = inspect.signature(IIso8583Model.to_iso_dict)
        assert sig.return_annotation is not inspect.Parameter.empty


class TestIMessageGeneratorProtocol:
    def test_has_generate_method(self):
        assert hasattr(IMessageGenerator, "generate")

    def test_has_parse_method(self):
        assert hasattr(IMessageGenerator, "parse")

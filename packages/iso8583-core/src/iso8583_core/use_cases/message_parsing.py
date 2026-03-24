"""
ISO 8583 メッセージ解析ユースケース。

アプリケーションのビジネスロジックを含むユースケース層。
特定のライブラリ（pyiso8583等）に依存せず、インターフェースを介して操作を行う。
"""
import logging
from typing import Type, TypeVar, cast

from iso8583_types.core.interfaces.iso_ports import IIso8583Model, IMessageGenerator
from iso8583_types.core.models.mti import Mti

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=IIso8583Model)


class ParseMessageUseCase:
    """ISO 8583 バイナリメッセージの解析をオーケストレーションするユースケース。"""

    def __init__(self, message_generator: IMessageGenerator) -> None:
        # 依存関係（Adapter）をコンストラクタで受け取る (DI: Dependency Injection)
        self.message_generator = message_generator

    def execute(self, raw_message: bytes, model_cls: Type[T]) -> tuple[Mti, T]:
        """
        ISO 8583 バイナリメッセージを解析し、MTI とモデルを返す。

        Args:
            raw_message: 解析対象の ISO 8583 バイト列
            model_cls: 解析結果を格納するモデルクラス

        Returns:
            (mti, model): パースされた MTI Value Object とモデルインスタンス

        Raises:
            MessageDecodeError: デコードに失敗した場合
        """
        logger.info("ISO 8583 メッセージ解析を開始します (bytes: %d)", len(raw_message))

        try:
            mti_str, model = self.message_generator.parse(raw_message, model_cls)
            mti = Mti.from_str(mti_str)

            logger.info("ISO 8583 メッセージ解析が正常に完了しました (MTI: %s)", mti.to_str())
            # IMessageGenerator.parse() はプロトコルのため戻り型が IIso8583Model に固定されているが、
            # model_cls を渡しているので実際は T のインスタンス。cast で型チェッカーに伝える。
            return mti, cast(T, model)
        except Exception as e:
            logger.error("ISO 8583 メッセージ解析中にエラーが発生しました: %s", str(e), exc_info=True)
            raise

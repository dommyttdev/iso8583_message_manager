import logging
from iso8583_types.interfaces.iso_ports import IMessageGenerator, IIso8583Model
from iso8583_types.models.mti import Mti

logger = logging.getLogger(__name__)

class GenerateMessageUseCase:
    """
    アプリケーションのビジネスロジックを含むユースケース層。
    特定のライブラリ（pyiso8583等）に依存せず、インターフェースを介して操作を行う。
    """
    
    def __init__(self, message_generator: IMessageGenerator):
        # 依存関係（Adapter）をコンストラクタで受け取る (DI: Dependency Injection)
        self.message_generator = message_generator

    def execute(self, mti: Mti, model_data: IIso8583Model) -> bytearray:
        """
        ISO8583メッセージの生成プロセスをオーケストレーションする。

        Args:
            mti: メッセージタイプID（Value Object）。バリデーションは Mti.from_str() 時点で実施済み。
            model_data: データエレメントを保持するモデル

        Returns:
            エンコードされた ISO 8583 バイト列
        """
        logger.info("ISO 8583 メッセージ生成を開始します (MTI: %s)", mti.to_str())

        try:
            # 実際のエンコード処理をアダプターへ委譲
            encoded_data = self.message_generator.generate(mti, model_data)
            
            logger.info("ISO 8583 メッセージ生成が正常に完了しました (bytes: %d)", len(encoded_data))
            return encoded_data
        except Exception as e:
            logger.error("ISO 8583 メッセージ生成中にエラーが発生しました: %s", str(e), exc_info=True)
            # 再スローして上位層にエラーを伝える
            raise

from iso8583_manager.core.interfaces.iso_ports import IMessageGenerator, IIso8583Model

class GenerateMessageUseCase:
    """
    アプリケーションのビジネスロジックを含むユースケース層。
    特定のライブラリ（pyiso8583等）に依存せず、インターフェースを介して操作を行う。
    """
    
    def __init__(self, message_generator: IMessageGenerator):
        # 依存関係（Adapter）をコンストラクタで受け取る (DI: Dependency Injection)
        self.message_generator = message_generator

    def execute(self, mti: str, model_data: IIso8583Model) -> bytearray:
        """
        ISO8583メッセージの生成プロセスをオーケストレーションする。
        """
        if not mti or len(mti) != 4 or not mti.isdigit():
            raise ValueError("MTI must be exactly 4 characters.")
            
        # 今後の拡張ポイント（前処理、監査ログ出力など）
        
        # 実際のエンコード処理をアダプターへ委譲
        encoded_data = self.message_generator.generate(mti, model_data)
        
        # 今後の拡張ポイント（後処理、永続化など）
        
        return encoded_data

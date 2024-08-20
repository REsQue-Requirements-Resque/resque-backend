from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime


class SoftDeleteMixin:
    """모델에 소프트 삭제 기능을 추가하는 믹스인 클래스.

    이 클래스는 `is_deleted` 필드를 포함하여,
    모델 인스턴스가 실제로 삭제되지 않고 논리적으로만 삭제되었음을 기록할 수 있게 합니다.
    이를 통해 데이터베이스에서 데이터는 유지되지만, 애플리케이션에서는 삭제된 것으로 간주할 수 있습니다.

    Attributes:
        is_deleted (Mapped[bool]): 인스턴스가 삭제되었는지를 나타내는 플래그입니다.
        기본값은 `False`이며, 인스턴스가 삭제되지 않았음을 의미합니다.
    """

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        """소프트 삭제 플래그 필드를 정의합니다.

        이 필드는 인스턴스가 삭제되었는지를 나타내는 `Boolean` 타입의 필드입니다.
        기본값은 `False`이며, 삭제되지 않았음을 의미합니다.

        Returns:
            Mapped[bool]: 삭제 여부를 나타내는 불리언 필드입니다.
        """
        return mapped_column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime]:
        """소프트 삭제 시각 필드를 정의합니다.

        이 필드는 인스턴스가 삭제된 시각을 나타내는 `DateTime` 타입의 필드입니다.

        Returns:
            Mapped[datetime]: 삭제 시각을 나타내는 `DateTime` 필드입니다
        """
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            default=None,
        )

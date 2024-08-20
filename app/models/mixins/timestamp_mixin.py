from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, UTC


def set_now(tz=UTC):
    """현재 날짜 및 시간을 반환합니다.

    Args:
        tz (datetime.tzinfo): 시간대 정보. 기본값은 UTC입니다.

    Returns:
        datetime: 현재 날짜 및 시간을 포함하는 datetime 객체.
    """
    return datetime.now(tz)


class TimestampMixin:
    """모델에 타임스탬프 관련 필드를 추가하는 믹스인 클래스.

    이 클래스는 `created_at` 및 `updated_at` 필드를 포함하여,
    모델 인스턴스가 생성되거나 업데이트될 때 타임스탬프를 자동으로 기록합니다.

    Attributes:
        created_at (Mapped[datetime]): 인스턴스가 생성된 시각을 기록합니다.
        updated_at (Mapped[datetime]): 인스턴스가 마지막으로 업데이트된 시각을 기록합니다.
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: set_now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: set_now(UTC),
        onupdate=lambda: set_now(UTC),
    )

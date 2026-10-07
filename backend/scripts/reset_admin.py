# -*- coding: utf-8 -*-
r"""
重置管理员密码（忘记密码时使用，由「8-重置管理员密码.bat」调用）

说明：密码以加密形式存于数据库，无法"找回"，只能"重置"。
运行后按提示输入两次新密码即可（输入时屏幕不显示，属正常现象）。
"""
import getpass
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import User  # noqa: E402


def main() -> int:
    print(f"将重置管理员账号「{settings.admin_username}」的密码\n")

    pw1 = getpass.getpass("请输入新密码（输入时不显示）：")
    if not pw1:
        print("\n[错误] 密码不能为空")
        return 1
    if len(pw1) < 6:
        print("\n[错误] 密码太短了，至少 6 位")
        return 1
    pw2 = getpass.getpass("请再输入一次新密码：")
    if pw1 != pw2:
        print("\n[错误] 两次输入不一致，未做任何修改")
        return 1

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.admin_username).first()
        if admin is None:
            print(f"\n[提示] 管理员账号不存在，正在创建……")
            admin = User(username=settings.admin_username, role="admin")
            db.add(admin)
        admin.password_hash = hash_password(pw1)
        db.commit()
        print(f"\n[完成] 管理员「{settings.admin_username}」的密码已重置，请用新密码登录")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

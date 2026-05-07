from fastapi import APIRouter
from app.api.v1 import common
from app.api.v1 import admin
from app.api.v1 import audit_log
from app.api.v1 import auth
from app.api.v1 import device
from app.api.v1 import users
from app.api.v1 import detection
from app.api.v1 import detection_ws
from app.api.v1 import roles
from app.api.v1 import departments
from app.api.v1 import titles
from app.api.v1 import message
from app.api.v1 import export

router = APIRouter()

router.include_router(common.router, prefix="/common", tags=["common"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(audit_log.router, prefix="/audit-logs", tags=["audit-logs"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(device.router, tags=["device"])
router.include_router(users.router, tags=["users"])
router.include_router(detection.router, tags=["detection"])
router.include_router(detection_ws.router, tags=["detection-ws"])
router.include_router(roles.router, tags=["roles"])
router.include_router(departments.router, tags=["departments"])
router.include_router(titles.router, tags=["titles"])
router.include_router(message.router, tags=["message"])
router.include_router(export.router, tags=["export"])

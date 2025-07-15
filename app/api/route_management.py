from fastapi import FastAPI

from api.ui_api.v1alpha1 import abend as ui_abend
from api.ui_api.v1alpha1 import sop as ui_sop
from api.internal_api.v1alpha1 import abend as internal_abend
from api.internal_api.v1alpha1 import sop as internal_sop
from api import healthz, readyz, tags


def ui_routers(app: FastAPI):
    app.include_router(
        ui_abend.router,
        prefix="/adr/ui/v1alpha1/abend",
    )
    app.include_router(
        ui_sop.router,
        prefix="/adr/ui/v1alpha1/sop",
    )

def internal_routers(app: FastAPI):
    app.include_router(
        internal_abend.router,
        prefix="/adr/internal/v1alpha1/abend",
    )
    app.include_router(
        internal_sop.router,
        prefix="/adr/internal/v1alpha1/sop",
    )
    # Include health and readiness checks
    app.include_router(
        healthz.router,
        prefix="/healthz",
    )
    app.include_router(
        readyz.router,
        prefix="/readyz",
    )


# ROUTE_VISIBILITY: Dict[str, List[Any]] = {
#     tags.ApiType.UI.value: [
#         tags.UI_ABEND_V1ALPHA1,
#         tags.UI_SOP_V1ALPHA1
#     ],
#     tags.ApiType.INTERNAL.value: [
#         tags.INTERNAL_ABEND_V1ALPHA1,
#         tags.INTERNAL_SOP_V1ALPHA1
#     ],
#     tags.ApiType.SYSTEM.value: [
#         tags.HEALTHZ,
#         tags.READYZ
#     ],
#     tags.ApiType.ALL.value: [
#         tags.HEALTHZ,
#         tags.READYZ,
#         tags.UI_ABEND_V1ALPHA1,
#         tags.UI_SOP_V1ALPHA1,
#         tags.INTERNAL_ABEND_V1ALPHA1,
#         tags.INTERNAL_SOP_V1ALPHA1
#     ]
# }

def initialize_api_routes(app: FastAPI, api_mode: str = "all"):
    """
    Include routes based on the API mode.
    
    :param app: FastAPI application instance
    :param api_mode: Mode of API to include routes for (default is "all")
    """
    if api_mode == tags.ApiType.UI.value:
        ui_routers(app)
    elif api_mode == tags.ApiType.INTERNAL.value:
        internal_routers(app)
    else:
        ui_routers(app)
        internal_routers(app)
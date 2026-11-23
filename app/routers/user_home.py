from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.services import listings


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    browse_result = listings.browse_for_students(
        user.id,
        area=None,
        max_price=None,
        amenity=None,
    )
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "listings": browse_result.get("listings", []) if browse_result.get("ok") else [],
        }
    )
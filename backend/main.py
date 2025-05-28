# Add this new route after the existing routes

@app.post("/update_nutrition")
async def update_nutrition(
    request: Request,
    calories: int = Form(None),
    diet_type: str = Form(None),
    protein_grams: int = Form(None),
    carbs_grams: int = Form(None),
    fat_grams: int = Form(None),
    nutrition_notes: str = Form(None)
):
    try:
        UserService().update_nutrition_preferences(
            request,
            calories,
            diet_type,
            protein_grams,
            carbs_grams,
            fat_grams,
            nutrition_notes
        )
        return RedirectResponse(
            "/account_settings?tab=nutritionTab&success=Nutrition preferences updated successfully",
            status_code=303
        )
    except Exception as e:
        template_data = {
            "request": request,
            "nutrition_error": str(e),
            "active_tab": "nutritionTab"
        }
        user_data = UserService().get_user_data_from_request(request)
        return templates.TemplateResponse("account_settings.html", {**template_data, **user_data})
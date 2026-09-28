import sys, re

filepath = r'c:\Users\rayyan\Desktop\generative-ai-techwiz-main\routers\warranty.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
async def _process_complaint_bg(complaint_dict, new_id, total_count, sentiment_data):
    def blocking_pipeline():
        try:
            genai_out = genai_pipeline.generate_intelligence(complaint_dict)
            ground_truth = python_validation_pipeline.validate_complaint(complaint_dict)
            comp_result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, complaint_dict)

            complaint_dict["genai_analysis"] = genai_out.model_dump()
            complaint_dict["ground_truth"] = ground_truth.model_dump()
            complaint_dict["comparison"] = comp_result.model_dump()
            complaint_dict["status"] = "Analyzed" if not comp_result.requires_manual_review else "Manual Review Required"
            complaint_dict["category"] = ground_truth.expected_category
            complaint_dict["subcategory"] = ground_truth.expected_subcategory
            complaint_dict["department"] = ground_truth.expected_department
            complaint_dict["urgency"] = ground_truth.expected_urgency
            complaint_dict["priority"] = ground_truth.expected_priority
        except Exception as e:
            logger.error(f"Error executing dual pipeline on complaint {new_id}: {e}")
            complaint_dict["status"] = "New"

        complaints_col = get_complaints_col()
        # Update the existing record instead of inserting a new one
        complaints_col.update_one({"complaint_id": new_id}, {"$set": complaint_dict})
        
        audit_col = get_audit_logs_col()
        audit_col.insert_one({
            "log_id": f"AUD-{total_count+1:05d}",
            "complaint_id": new_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actor": "AI_Dual_Pipeline",
            "action": "Analyzed & Verified",
            "details": {"status": complaint_dict.get("status"), "verification": complaint_dict.get("comparison", {}).get("verification_status")}
        })
        return complaint_dict

    updated_dict = await run_in_threadpool(blocking_pipeline)

    try:
        await ws_manager.broadcast({
            "type": "NEW_COMPLAINT",
            "complaint_id": new_id,
            "customer_name": updated_dict["customer_name"],
            "complaint_title": updated_dict["complaint_title"],
            "category": updated_dict.get("category", "General"),
            "urgency": updated_dict.get("urgency", "Medium"),
            "priority": updated_dict.get("priority", "P2"),
            "status": updated_dict.get("status", "New"),
            "sentiment": sentiment_data,
            "timestamp": updated_dict["created_at"]
        })
    except Exception as e:
        logger.error(f"Error broadcasting WebSocket event: {e}")

@router.post("/complaints/submit")
async def submit_complaint(
    request: Request,
    background_tasks: BackgroundTasks,
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_phone: Optional[str] = Form(None),
    customer_type: str = Form("Standard"),
    complaint_title: str = Form(...),
    complaint_description: str = Form(...),
    product_or_service: Optional[str] = Form(None),
    order_reference: Optional[str] = Form(None),
    preferred_channel: str = Form("Web Form")
):
    current_user = AuthManager.get_current_user(request)
    
    is_valid, err_msg = ComplaintPreprocessor.validate_complaint_input(complaint_title, complaint_description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    complaints_col = get_complaints_col()
    content_hash = ComplaintPreprocessor.compute_content_hash(complaint_description)
    
    is_dup = False
    dup_id = None
    existing = complaints_col.find_one({"content_hash": content_hash})
    if existing:
        is_dup = True
        dup_id = existing.get("complaint_id")

    total_count = complaints_col.count_documents({})
    new_id = f"CMP-{total_count + 1:05d}"
    
    prod_meta = None
    if product_or_service:
        prod_meta = ProductCatalog.find_product(product_or_service)

    sentiment_data = SentimentTelemetryEngine.analyze(
        complaint_title,
        complaint_description,
        customer_type
    )

    user_id = current_user.get("user_id") if current_user else None
    user_avatar = current_user.get("avatar") if current_user else None

    complaint_dict = {
        "complaint_id": new_id,
        "customer_id": f"CUST-{1000 + total_count + 1}",
        "user_id": user_id,
        "user_avatar": user_avatar,
        "customer_name": customer_name.strip(),
        "customer_email": customer_email.strip().lower(),
        "customer_phone": customer_phone.strip() if customer_phone else None,
        "customer_type": customer_type,
        "complaint_title": complaint_title.strip(),
        "complaint_description": complaint_description.strip(),
        "product_or_service": product_or_service.strip() if product_or_service else "General Item",
        "product_metadata": prod_meta,
        "order_reference": order_reference.strip() if order_reference else None,
        "preferred_channel": preferred_channel,
        "content_hash": content_hash,
        "is_duplicate": is_dup,
        "duplicate_of_id": dup_id,
        "sentiment_telemetry": sentiment_data,
        "status": "AI Pipeline Processing",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # IMPORTANT: Insert synchronously first so it is immediately trackable by the user!
    complaints_col.insert_one(complaint_dict.copy())

    background_tasks.add_task(_process_complaint_bg, complaint_dict, new_id, total_count, sentiment_data)

    return {
        "success": True,
        "complaint_id": new_id,
        "message": "Your complaint has been officially registered with NovaTech Customer Support Operations. AI is currently analyzing your ticket.",
        "status": "AI Pipeline Processing",
        "submitted_at": complaint_dict["created_at"]
    }
"""

pattern = re.compile(r'async def _process_complaint_bg.*?return \{\n        \"success\": True,.*?\"submitted_at\": complaint_dict\[\"created_at\"\]\n    \}', re.DOTALL)
new_content = pattern.sub(replacement, content)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Database insertion logic patched.')

import pytest


async def test_create_repair_task_with_stages(ac):

    train_res = await ac.post("/api/v1/rolling-stocks/", json={
        "inventory_number": "0034",
        "series": "ЭД4М",
        "manufacture_date": "2015-05-10"
    })
    assert train_res.status_code == 201
    train_id = train_res.json()["id"]

    brigade_res = await ac.post("/api/v1/catalogs/brigades", json={
        "name": "Бригада ТО-1",
        "master_name": "Петров П.П.",
        "master_id_number": "1112223"
    })
    assert brigade_res.status_code == 201
    brigade_id = brigade_res.json()["id"]

    reg_res = await ac.post("/api/v1/catalogs/regulations", json={
        "repair_type": "ТО-1",
        "train_series": "ЭД4М",
        "standard_hours": 2,
        "frequency_days": 1,
        "templates": [
            {"name": "Осмотр подвагонного оборудования", "order_number": 1},
            {"name": "Проверка тормозной системы", "order_number": 2}
        ]
    })
    assert reg_res.status_code == 201

    task_res = await ac.post("/api/v1/repair-tasks/", json={
        "rolling_stock_id": train_id,
        "repair_type": "ТО-1",
        "brigade_id": brigade_id
    })

    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    full_task_res = await ac.get(f"/api/v1/repair-tasks/{task_id}/full")
    assert full_task_res.status_code == 200

    full_task = full_task_res.json()

    assert full_task["rolling_stock_id"] == train_id
    assert full_task["status"] == "Создано"

    stages = full_task.get("stages", [])
    assert len(stages) == 2, "Должно сгенерироваться ровно 2 этапа из регламента"

    assert stages[0]["name"] == "Осмотр подвагонного оборудования"
    assert stages[0]["status"] == "Ожидание"

    assert stages[1]["name"] == "Проверка тормозной системы"
    assert stages[1]["status"] == "Ожидание"
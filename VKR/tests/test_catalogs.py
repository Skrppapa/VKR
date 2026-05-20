import pytest


async def test_create_brigade(ac):
    """Проверка успешного создания бригады"""
    response = await ac.post("/api/v1/catalogs/brigades", json={
        "name": "Бригада №1",
        "master_name": "Иванов И.И.",
        "master_id_number": "1234567"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Бригада №1"
    assert "id" in data


async def test_create_brigade_validation_error(ac):
    """Проверка отсечения неверных данных Pydantic-схемой"""
    response = await ac.post("/api/v1/catalogs/brigades", json={
        "name": "Бригада №2",
        "master_name": "Петров П.П.",
        "master_id_number": "12345AB"  # Ошибка здесь
    })

    assert response.status_code == 422


async def test_get_brigades_list(ac):
    """Проверка получения списка бригад"""
    await ac.post("/api/v1/catalogs/brigades", json={
        "name": "Бригада №3",
        "master_name": "Сидоров С.С.",
        "master_id_number": "7654321"
    })

    response = await ac.get("/api/v1/catalogs/brigades")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Бригада №3"
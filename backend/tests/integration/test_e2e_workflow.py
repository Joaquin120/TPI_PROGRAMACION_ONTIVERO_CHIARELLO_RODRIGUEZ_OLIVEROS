from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest


@pytest.mark.asyncio
async def test_complete_e2e_journey(async_client: httpx.AsyncClient) -> None:
    """Validates the complete end-to-end journey from health probes through full CRUD lifecycle."""
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = MagicMock()
    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    # 1. Verify health probes
    with patch("src.api.v1.endpoints.health.engine", mock_engine):
        # Liveness probe
        liveness_res = await async_client.get("/health/live")
        assert liveness_res.status_code == 200
        liveness_data = liveness_res.json()
        assert liveness_data["status"] in ("healthy", "alive")

        # Readiness probe
        readiness_res = await async_client.get("/health/ready")
        assert readiness_res.status_code == 200
        readiness_data = readiness_res.json()
        assert readiness_data["status"] == "ready"
        assert readiness_data["database"] == "connected"

    # 2. Create an item (POST /api/v1/items/)
    item_payload = {
        "name": "E2E Master Product",
        "description": "End-to-end verification item",
        "price": 199.99,
        "stock": 15,
        "is_active": True,
    }
    create_res = await async_client.post("/api/v1/items/", json=item_payload)
    assert create_res.status_code == 201
    created_item = create_res.json()
    item_id = created_item["id"]
    assert created_item["name"] == item_payload["name"]
    assert created_item["price"] == item_payload["price"]
    assert created_item["stock"] == item_payload["stock"]
    assert created_item["is_active"] is True
    assert "created_at" in created_item
    assert "updated_at" in created_item

    # 3. List items paginated and confirm the item is in the list (GET /api/v1/items/)
    list_res = await async_client.get("/api/v1/items/?skip=0&limit=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    found_item = next((it for it in list_data["items"] if it["id"] == item_id), None)
    assert found_item is not None
    assert found_item["name"] == "E2E Master Product"

    # 4. Retrieve the created item by ID (GET /api/v1/items/{item_id})
    get_res = await async_client.get(f"/api/v1/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "E2E Master Product"

    # 5. Partially update the item (PATCH /api/v1/items/{item_id})
    patch_payload = {"price": 179.99, "stock": 10}
    patch_res = await async_client.patch(f"/api/v1/items/{item_id}", json=patch_payload)
    assert patch_res.status_code == 200
    patched_item = patch_res.json()
    assert patched_item["price"] == 179.99
    assert patched_item["stock"] == 10
    assert patched_item["name"] == "E2E Master Product"

    # 6. Delete the item (DELETE /api/v1/items/{item_id})
    del_res = await async_client.delete(f"/api/v1/items/{item_id}")
    assert del_res.status_code == 204

    # 7. Confirm the item is gone (GET /api/v1/items/{item_id} -> 404)
    gone_res = await async_client.get(f"/api/v1/items/{item_id}")
    assert gone_res.status_code == 404
    assert gone_res.json()["detail"] == "Item not found"

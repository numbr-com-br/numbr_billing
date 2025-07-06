import pytest
import pytest_asyncio
from httpx import AsyncClient
from decimal import Decimal
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Plan, RevenueRange, PlanPricing, Addon
from src.enums import BillingCycle, AddonType


@pytest_asyncio.fixture
async def setup_pricing_data(db: AsyncSession):
    # Create revenue ranges
    ranges = [
        RevenueRange(
            name="Microempresa",
            min_revenue=Decimal("0"),
            max_revenue=Decimal("360000"),
            sort_order=1
        ),
        RevenueRange(
            name="Pequena Empresa",
            min_revenue=Decimal("360000.01"),
            max_revenue=Decimal("4800000"),
            sort_order=2
        )
    ]
    
    for range_obj in ranges:
        db.add(range_obj)
    await db.commit()
    
    # Create plan
    plan = Plan(
        name="Starter",
        description="Plano inicial",
        cycle=BillingCycle.MONTHLY,
        features=["Feature 1", "Feature 2"]
    )
    db.add(plan)
    await db.commit()
    
    # Create plan pricing
    for i, range_obj in enumerate(ranges):
        pricing = PlanPricing(
            plan_id=plan.id,
            revenue_range_id=range_obj.id,
            price=Decimal("50") * (i + 1)
        )
        db.add(pricing)
    
    # Create addon
    addon = Addon(
        name="Extra Users",
        description="Add more users",
        price=Decimal("20"),
        type=AddonType.ONE_TIME
    )
    db.add(addon)
    await db.commit()
    
    return {
        "plan": plan,
        "ranges": ranges,
        "addon": addon
    }


@pytest.mark.asyncio
async def test_get_plans_with_pricing(client: AsyncClient, db: AsyncSession, setup_pricing_data):
    response = await client.get("/api/checkout/plans")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    plan = data[0]
    
    assert plan["name"] == "Starter"
    assert len(plan["pricing"]) == 2
    
    # Check pricing details
    pricing = plan["pricing"]
    assert pricing[0]["revenue_range_name"] == "Microempresa"
    assert Decimal(pricing[0]["price"]) == Decimal("50")
    assert pricing[1]["revenue_range_name"] == "Pequena Empresa"
    assert Decimal(pricing[1]["price"]) == Decimal("100")


@pytest.mark.asyncio
async def test_get_revenue_ranges(client: AsyncClient, db: AsyncSession, setup_pricing_data):
    response = await client.get("/api/checkout/revenue-ranges")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert data[0]["name"] == "Microempresa"
    assert data[1]["name"] == "Pequena Empresa"


@pytest.mark.asyncio
async def test_start_checkout_with_revenue(client: AsyncClient, db: AsyncSession, setup_pricing_data):
    data = setup_pricing_data
    
    with patch("src.services.asaas.asaas_service.create_customer") as mock_create_customer, \
         patch("src.services.asaas.asaas_service.create_subscription") as mock_create_subscription:
        
        mock_create_customer.return_value = {"id": "cus_test123"}
        mock_create_subscription.return_value = {
            "id": "sub_test123",
            "nextDueDate": "2024-01-01"
        }
        
        checkout_data = {
            "plan_id": data["plan"].id,
            "addon_ids": [data["addon"].id],
            "customer": {
                "name": "Test Company",
                "email": "test@company.com",
                "cpf_cnpj": "12345678901",
                "phone": "11999999999",
                "annual_revenue": "300000"  # Microempresa range
            },
            "billing_type": "CREDIT_CARD"
        }
        
        response = await client.post("/api/checkout/start", json=checkout_data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Price should be plan price (50) + addon price (20) = 70
        assert Decimal(result["total_price"]) == Decimal("70")
        assert "payment_link" in result
        assert "subscription_id" in result


@pytest.mark.asyncio
async def test_start_checkout_without_revenue(client: AsyncClient, db: AsyncSession, setup_pricing_data):
    data = setup_pricing_data
    
    checkout_data = {
        "plan_id": data["plan"].id,
        "addon_ids": [],
        "customer": {
            "name": "Test Company",
            "email": "test2@company.com",
            "cpf_cnpj": "12345678902",
            "phone": "11999999999"
            # No annual_revenue provided
        },
        "billing_type": "BOLETO"
    }
    
    response = await client.post("/api/checkout/start", json=checkout_data)
    
    assert response.status_code == 400
    assert "Annual revenue is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_start_checkout_invalid_revenue_range(client: AsyncClient, db: AsyncSession, setup_pricing_data):
    data = setup_pricing_data
    
    checkout_data = {
        "plan_id": data["plan"].id,
        "addon_ids": [],
        "customer": {
            "name": "Test Company",
            "email": "test3@company.com",
            "cpf_cnpj": "12345678903",
            "phone": "11999999999",
            "annual_revenue": "10000000"  # Above configured ranges
        },
        "billing_type": "PIX"
    }
    
    response = await client.post("/api/checkout/start", json=checkout_data)
    
    assert response.status_code == 400
    assert "No pricing available" in response.json()["detail"]
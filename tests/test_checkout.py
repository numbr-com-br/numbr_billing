import pytest
from decimal import Decimal
from unittest.mock import patch
from sqlalchemy.orm import Session

from src.models import Plan, RevenueRange, PlanPricing, Addon
from src.enums import BillingCycle, AddonType


@pytest.fixture
def setup_pricing_data(db: Session):
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
    db.commit()
    
    # Create plan
    plan = Plan(
        name="Starter",
        description="Plano inicial",
        cycle=BillingCycle.MONTHLY,
        features=["Feature 1", "Feature 2"]
    )
    db.add(plan)
    db.commit()
    
    # Create plan pricing
    for i, range_obj in enumerate(ranges):
        pricing = PlanPricing(
            plan_id=plan.id,
            revenue_range_id=range_obj.id,
            price=Decimal("50") * (i + 1)
        )
        db.add(pricing)
    db.commit()
    
    # Create addons
    addon1 = Addon(
        name="Extra Users",
        description="Add more users",
        type=AddonType.PER_UNIT,
        price=Decimal("10")
    )
    addon2 = Addon(
        name="Premium Support",
        description="24/7 support",
        type=AddonType.FIXED,
        price=Decimal("50")
    )
    db.add(addon1)
    db.add(addon2)
    db.commit()
    
    return {
        "plan": plan,
        "ranges": ranges,
        "addons": [addon1, addon2]
    }


def test_get_plans_with_pricing(client, setup_pricing_data):
    """Test getting plans with their pricing tiers"""
    response = client.get("/api/checkout/plans")
    
    assert response.status_code == 200
    plans = response.json
    assert len(plans) == 1
    
    plan = plans[0]
    assert plan["name"] == "Starter"
    assert len(plan["pricing"]) == 2
    assert plan["pricing"][0]["price"] == "50.00"
    assert plan["pricing"][1]["price"] == "100.00"


def test_get_addons(client, setup_pricing_data):
    """Test getting available addons"""
    response = client.get("/api/checkout/addons")
    
    assert response.status_code == 200
    addons = response.json
    assert len(addons) == 2
    assert addons[0]["name"] == "Extra Users"
    assert addons[1]["name"] == "Premium Support"


def test_get_revenue_ranges(client, setup_pricing_data):
    """Test getting revenue ranges"""
    response = client.get("/api/checkout/revenue-ranges")
    
    assert response.status_code == 200
    ranges = response.json
    assert len(ranges) == 2
    assert ranges[0]["name"] == "Microempresa"
    assert ranges[1]["name"] == "Pequena Empresa"


@patch('src.services.asaas.AsaasService.create_customer')
@patch('src.services.asaas.AsaasService.create_subscription')
def test_start_checkout(mock_create_subscription, mock_create_customer, client, setup_pricing_data):
    """Test starting checkout process"""
    # Mock Asaas responses
    mock_create_customer.return_value = {
        "id": "cus_test123",
        "name": "Test Customer",
        "email": "test@example.com"
    }
    
    mock_create_subscription.return_value = {
        "id": "sub_test123",
        "customer": "cus_test123",
        "billingType": "CREDIT_CARD",
        "value": 50.0,
        "nextDueDate": "2024-01-01",
        "status": "PENDING"
    }
    
    # Prepare request data
    data = setup_pricing_data
    checkout_data = {
        "customer": {
            "name": "Test Customer",
            "email": "test@example.com",
            "cpf_cnpj": "12345678901",
            "phone": "11999999999",
            "annual_revenue": "100000"
        },
        "plan_id": data["plan"].id,
        "addon_ids": [data["addons"][0].id],
        "billing_type": "CREDIT_CARD"
    }
    
    response = client.post(
        "/api/checkout/start",
        json=checkout_data,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    result = response.json
    assert "subscription_id" in result
    assert "payment_link" in result
    
    # Verify mocks were called
    mock_create_customer.assert_called_once()
    mock_create_subscription.assert_called_once()


def test_start_checkout_missing_revenue(client, setup_pricing_data):
    """Test checkout fails without annual revenue"""
    data = setup_pricing_data
    checkout_data = {
        "customer": {
            "name": "Test Customer",
            "email": "test@example.com",
            "cpf_cnpj": "12345678901",
            "phone": "11999999999"
            # Missing annual_revenue
        },
        "plan_id": data["plan"].id,
        "addon_ids": [],
        "billing_type": "CREDIT_CARD"
    }
    
    response = client.post(
        "/api/checkout/start",
        json=checkout_data,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 400
    assert "annual_revenue is required" in response.json["error"]
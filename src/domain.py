"""
TRUCKLY — domain model and the single cost model.

The cost model lives here and ONLY here. Every policy calls the same object,
so no policy can accidentally be evaluated with different fuel prices,
different wages or a different fuel curve. This is what makes the four-way
policy comparison in simulation.py a fair test.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class Shipment:
    shipment_id: str
    origin: str
    dest: str
    weight_kg: float
    volume_m3: float
    ready_time_hr: float          # hours from instance t0
    deadline_hr: float
    service_pickup_min: float
    service_delivery_min: float
    direct_km: float
    direct_min: float
    revenue_inr: float


@dataclass
class Truck:
    truck_id: str
    truck_type: str
    capacity_kg: float
    capacity_m3: float
    base_fuel: float              # L/100km unladen
    load_coeff: float             # L/100km per tonne
    current_node: str
    home_node: str
    available_from_hr: float
    must_return_by_hr: float
    driving_hours_used: float
    driver_id: str
    direct_return_km: float
    direct_return_min: float


@dataclass
class Leg:
    """One arc of an executed route."""
    frm: str
    to: str
    km: float
    minutes: float
    payload_t: float
    road_factor: float
    fuel_l: float


@dataclass
class Journey:
    truck_id: str
    policy: str
    matched: List[str] = field(default_factory=list)
    legs: List[Leg] = field(default_factory=list)
    route: List[str] = field(default_factory=list)
    waiting_hr: float = 0.0
    service_hr: float = 0.0
    late_deliveries: int = 0
    lateness_min: float = 0.0
    feasible: bool = True
    unmatched_reason: str = "matched"
    match_score: float = float("nan")
    solve_ms: float = 0.0


class CostModel:
    def __init__(self, cfg):
        c = cfg["cost"]
        f = cfg["fuel_model"]
        self.diesel = c["diesel_price_inr_per_litre"]
        self.toll_km = c["toll_inr_per_km"]
        self.wage_hr = c["driver_wage_inr_per_hour"]
        self.fixed = c["fixed_cost_inr_per_trip"]
        self.wait_mult = c["waiting_cost_multiplier"]
        self.co2_per_l = c["co2_kg_per_litre_diesel"]
        self.lambda_empty = c.get("empty_km_penalty_inr_per_km", 0.0)
        self.gamma = f["road_factor_coeff_gamma"]
        self.sigma = f["noise_lognormal_sigma"]

    # -- fuel ---------------------------------------------------------------
    def arc_fuel_litres(self, km, payload_t, base, coeff, road_factor, eps=1.0):
        """Load-dependent, condition-perturbed consumption.

        F = (d/100) * (beta0 + beta1*w + gamma*rho) * eps

        The load term is what makes an empty kilometre genuinely cheaper than a
        loaded one without making it free -- which is the entire economic
        premise of backhaul matching.
        """
        rate = base + coeff * payload_t + self.gamma * road_factor
        return (km / 100.0) * rate * eps

    # -- journey roll-up -----------------------------------------------------
    def summarise(self, j: Journey, truck: Truck, revenue=0.0):
        total_km = sum(l.km for l in j.legs)
        loaded_km = sum(l.km for l in j.legs if l.payload_t > 1e-9)
        empty_km = total_km - loaded_km
        drive_hr = sum(l.minutes for l in j.legs) / 60.0
        fuel = sum(l.fuel_l for l in j.legs)
        payload_tkm = sum(l.km * l.payload_t for l in j.legs)
        cap_tkm = (truck.capacity_kg / 1000.0) * total_km

        duty_hr = drive_hr + j.service_hr + j.waiting_hr
        fuel_cost = fuel * self.diesel
        driver_cost = (drive_hr + j.service_hr) * self.wage_hr \
                      + j.waiting_hr * self.wage_hr * self.wait_mult
        toll = total_km * self.toll_km
        variable = fuel_cost + driver_cost + toll
        total_cost = variable + self.fixed

        return dict(
            total_distance_km=total_km,
            loaded_distance_km=loaded_km,
            empty_distance_km=empty_km,
            detour_distance_km=total_km - truck.direct_return_km,
            payload_tonne_km=payload_tkm,
            capacity_tonne_km=cap_tkm,
            utilisation_weight_pct=(100.0 * payload_tkm / cap_tkm) if cap_tkm > 0 else 0.0,
            utilisation_distance_pct=(100.0 * loaded_km / total_km) if total_km > 0 else 0.0,
            driving_time_hr=drive_hr,
            service_time_hr=j.service_hr,
            waiting_time_hr=j.waiting_hr,
            duty_time_hr=duty_hr,
            fuel_litres=fuel,
            fuel_cost_inr=fuel_cost,
            driver_cost_inr=driver_cost,
            toll_cost_inr=toll,
            variable_cost_inr=variable,
            fixed_cost_inr=self.fixed,
            total_cost_inr=total_cost,
            revenue_inr=revenue,
            net_cost_inr=total_cost - revenue,
            co2_kg=fuel * self.co2_per_l,
            avg_payload_tonnes=(payload_tkm / loaded_km) if loaded_km > 1e-9 else 0.0,
            n_shipments_matched=len(j.matched),
            late_deliveries=j.late_deliveries,
            lateness_minutes=j.lateness_min,
        )

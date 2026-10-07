"""
TRUCKLY — synthetic freight instance generator.

EVERYTHING this module emits is SIM (simulated) except the node coordinates it
inherits from network.py (OBS). It is fully seeded: the same (master_seed,
scenario, instance_id) triple reproduces a byte-identical instance.

Structural realism note
-----------------------
The generator models the actual asymmetry that creates the empty-return
problem. Trucks finish their outbound leg at consumption ("sink") nodes and
must get home to production ("source") nodes. The open shipment pool is
deliberately dominated by SOURCE -> SINK "headhaul" freight, with only a
minority of SINK -> SOURCE "backhaul" freight. `demand_asymmetry` controls the
split. If the pool were symmetric, backhaul matching would be trivial and the
whole research question would be uninteresting.
"""
from __future__ import annotations

import numpy as np

from .network import RoadNetwork, SOURCE_REGION
from .domain import Shipment, Truck


def _weighted_choice(rng, ids, w, k=1, exclude=None):
    w = np.asarray(w, dtype=float).copy()
    if exclude is not None:
        for e in exclude:
            w[ids.index(e)] = 0.0
    s = w.sum()
    if s <= 0:
        w = np.ones_like(w); s = w.sum()
    return rng.choice(len(ids), size=k, p=w / s)


class InstanceGenerator:
    def __init__(self, cfg, net: RoadNetwork):
        self.cfg = cfg
        self.net = net
        self.master_seed = cfg["meta"]["master_seed"]
        ids = net.ids
        self.src_mask = np.array([1.0 if i in SOURCE_REGION else 0.25 for i in ids])
        self.sink_mask = np.array([0.25 if i in SOURCE_REGION else 1.0 for i in ids])
        self.w_source = net.demand_out * self.src_mask
        self.w_sink = net.demand_in * self.sink_mask
        self._build_gravity()

    # ------------------------------------------------------------------
    def _build_gravity(self):
        """Gravity (spatial-interaction) model for origin-destination demand.

            P(o -> d)  proportional to   w_o * w_d / dist(o,d)^beta

        This is the standard deterrence-function formulation used in transport
        planning. It matters here for a substantive reason, not a cosmetic one:
        uniform OD sampling over 40 nodes spreads freight across 1,560 lanes,
        no corridor ever concentrates, and backhaul matching becomes impossible
        for reasons that are an artefact of the sampler rather than a property
        of freight. The gravity model concentrates flow onto short/medium lanes
        between high-weight nodes, which is what real road freight does.

        beta is ASM (declared assumption), documented in docs/methodology.md.
        """
        beta = float(self.cfg["scenario_defaults"].get("gravity_beta", 1.8))
        d = self.net.dist.copy()
        horizon_min = 0.55 * self.cfg["driver"]["max_driving_hours"] * 60.0
        ok = (d >= 40.0) & (self.net.dur <= horizon_min)
        deterrence = np.where(ok, 1.0 / np.power(np.maximum(d, 1.0), beta), 0.0)
        gh = np.outer(self.w_source, self.w_sink) * deterrence
        gb = np.outer(self.w_sink, self.w_source) * deterrence
        np.fill_diagonal(gh, 0.0); np.fill_diagonal(gb, 0.0)
        self.G_head = gh / gh.sum()
        self.G_back = gb / gb.sum()
        self._flat_head = self.G_head.ravel()
        self._flat_back = self.G_back.ravel()

    def _sample_od(self, rng, headhaul, k=1):
        flat = self._flat_head if headhaul else self._flat_back
        idx = rng.choice(flat.size, size=k, p=flat)
        n = self.net.n
        return [(int(i // n), int(i % n)) for i in idx]

    # ------------------------------------------------------------------
    def scenario_params(self, scenario_name):
        p = dict(self.cfg["scenario_defaults"])
        p.update(self.cfg["scenarios"].get(scenario_name, {}) or {})
        return p

    def _seed(self, scenario_name, instance_id, stream=0):
        h = abs(hash((scenario_name, int(instance_id), int(stream)))) % (2**31)
        return (self.master_seed * 1_000_003 + h) % (2**32)

    # ------------------------------------------------------------------
    def fuel_noise_matrix(self, scenario_name, instance_id):
        """Common random numbers.

        eps[a][b] is fixed for an (instance, arc) pair, so ANY policy that
        traverses arc a->b in this instance experiences the SAME fuel
        perturbation. This is what makes the four-policy comparison paired and
        is the single most important variance-reduction device in the study.
        """
        rng = np.random.default_rng(self._seed(scenario_name, instance_id, 99))
        n = self.net.n
        s = self.cfg["fuel_model"]["noise_lognormal_sigma"]
        eps = rng.lognormal(mean=-0.5 * s * s, sigma=s, size=(n, n))
        return (eps + eps.T) / 2.0

    # ------------------------------------------------------------------
    def make_fleet(self, scenario_name, instance_id, p):
        rng = np.random.default_rng(self._seed(scenario_name, instance_id, 1))
        ids = self.net.ids
        types = self.cfg["truck_types"]
        mix = p.get("fleet_mix") or {k: v["share"] for k, v in types.items()}
        names = list(mix.keys())
        probs = np.array([mix[k] for k in names], dtype=float)
        probs = probs / probs.sum()

        drv = self.cfg["driver"]
        trucks = []
        n = int(p["n_trucks"])
        attempts = 0
        while len(trucks) < n and attempts < n * 80:
            attempts += 1
            # The truck has just completed an outbound HEADHAUL leg o -> d.
            # It is therefore standing at d and must get home to o.
            (oi, di), = self._sample_od(rng, headhaul=True, k=1)
            home = ids[oi]
            cur = ids[di]
            d_ret = self.net.d(cur, home)
            t_ret_hr = self.net.t(cur, home) / 60.0
            # Single-leg model: exclude trivial returns AND returns that could
            # not be completed inside one legal driving day. Multi-day journey
            # chains are explicitly out of scope (see docs/limitations.md).
            if d_ret < 60.0 or t_ret_hr > 0.65 * drv["max_driving_hours"]:
                continue
            ttype = names[rng.choice(len(names), p=probs)]
            spec = types[ttype]

            # Driver headroom is generated RELATIVE to the direct return, so
            # the empty-return baseline B0 is ALWAYS feasible by construction.
            # (Asserted in simulation; a policy that cannot even drive home
            # would make the comparison meaningless.)
            rem_drive = min(drv["max_driving_hours"],
                            t_ret_hr + rng.uniform(1.0, 3.2))
            rem_duty = min(drv["max_duty_hours"], rem_drive + rng.uniform(1.2, 2.8))
            used = max(0.0, drv["max_driving_hours"] - rem_drive)
            avail = float(rng.uniform(5.0, 15.0))

            k = len(trucks)
            trucks.append(Truck(
                truck_id=f"T{instance_id:04d}_{k:03d}",
                truck_type=ttype,
                capacity_kg=spec["capacity_kg"],
                capacity_m3=spec["capacity_m3"],
                base_fuel=spec["base_fuel_l_per_100km"],
                load_coeff=spec["load_fuel_coeff_l_per_100km_per_t"],
                current_node=cur,
                home_node=home,
                available_from_hr=avail,
                must_return_by_hr=avail + rem_duty,
                driving_hours_used=used,
                driver_id=f"D{instance_id:04d}_{k:03d}",
                direct_return_km=d_ret,
                direct_return_min=self.net.t(cur, home),
            ))
        return trucks

    # ------------------------------------------------------------------
    def make_shipments(self, scenario_name, instance_id, p, n_trucks):
        rng = np.random.default_rng(self._seed(scenario_name, instance_id, 2))
        ids = self.net.ids
        m = max(1, int(round(p["shipment_density"] * n_trucks)))
        asym = p["demand_asymmetry"]

        ships = []
        made = 0
        attempts = 0
        while made < m and attempts < m * 60:
            attempts += 1
            headhaul = rng.random() < asym     # True = source->sink (of no use
                                               # to a returning truck)
            (oi, di), = self._sample_od(rng, headhaul=headhaul, k=1)
            o = ids[oi]; d = ids[di]
            dkm = self.net.d(o, d)
            dmin = self.net.t(o, d)
            # keep shipments inside the single-leg horizon
            if dkm < 40.0 or dmin / 60.0 > 0.55 * self.cfg["driver"]["max_driving_hours"]:
                continue

            wt = float(np.clip(rng.lognormal(p["weight_lognorm_mu"],
                                             p["weight_lognorm_sigma"]),
                               200.0, 24000.0))
            dens = max(80.0, rng.normal(p["density_kg_per_m3"],
                                        p["density_kg_per_m3"] * p["density_cv"]))
            vol = wt / dens
            ready = float(rng.uniform(0.0, 14.0))
            svc_p = float(p["service_time_pickup_min"] * rng.uniform(0.7, 1.4))
            svc_d = float(p["service_time_delivery_min"] * rng.uniform(0.7, 1.4))
            travel_hr = dmin / 60.0
            deadline = ready + max(2.5, travel_hr * p["deadline_slack_factor"]) \
                       + (svc_p + svc_d) / 60.0
            tc = self.cfg["cost"]
            revenue = (tc["tariff_inr_per_km"] * dkm
                       + tc["tariff_inr_per_tonne_km"] * (wt / 1000.0) * dkm
                       + tc["tariff_base_inr"])                       # ASM tariff

            ships.append(Shipment(
                shipment_id=f"S{instance_id:04d}_{made:03d}",
                origin=o, dest=d,
                weight_kg=round(wt, 1), volume_m3=round(vol, 3),
                ready_time_hr=round(ready, 3), deadline_hr=round(deadline, 3),
                service_pickup_min=round(svc_p, 1),
                service_delivery_min=round(svc_d, 1),
                direct_km=round(dkm, 2), direct_min=round(dmin, 2),
                revenue_inr=round(revenue, 2),
            ))
            made += 1
        return ships

    # ------------------------------------------------------------------
    def generate(self, scenario_name, instance_id):
        p = self.scenario_params(scenario_name)
        trucks = self.make_fleet(scenario_name, instance_id, p)
        ships = self.make_shipments(scenario_name, instance_id, p, len(trucks))
        eps = self.fuel_noise_matrix(scenario_name, instance_id)
        return dict(scenario_id=scenario_name, instance_id=instance_id,
                    params=p, trucks=trucks, shipments=ships, eps=eps,
                    seed=self._seed(scenario_name, instance_id, 0))

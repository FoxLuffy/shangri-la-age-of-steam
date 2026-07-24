import asyncio
import json
import logging
import random

from backend.database import Faction, FactionStanding, Location, ResourceMarket, WorldState, get_session
from backend.engine import world_tick
from sqlalchemy import func
from sqlmodel import select

logger = logging.getLogger(__name__)

async def world_simulation_loop():
    while True:
        try:
            await world_tick()
            await asyncio.sleep(60)  # Tick every 60 seconds
        except asyncio.CancelledError:
            logger.info("World simulation loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in world simulation loop: {e}")
            await asyncio.sleep(60)

async def simulate_global_market(manager):
    while True:
        await asyncio.sleep(10)  # Update market every 10 seconds
        try:
            with get_session() as session:
                markets = session.exec(select(ResourceMarket)).all()
                if not markets:
                    # Initialize
                    for res in ["Brass", "Copper", "Aetherium", "Coal"]:
                        session.add(
                            ResourceMarket(resource_name=res, base_price=10.0, current_price=10.0, volatility=0.1)
                        )
                    session.commit()
                    markets = session.exec(select(ResourceMarket)).all()

                # Simulate global player actions fluctuating the market
                for m in markets:
                    # Random drift
                    drift = random.uniform(-m.volatility, m.volatility)
                    m.current_price = max(1.0, m.current_price * (1.0 + drift))

                    # Rare global spike (thousands of players buy)
                    if random.random() < 0.05:
                        m.current_price *= 1.5

                    session.add(m)
                session.commit()

                # Broadcast to clients
                markets_data = [{"name": m.resource_name, "price": round(m.current_price, 2)} for m in markets]
                await manager.broadcast(json.dumps({"type": "market_sync", "market": markets_data}))
        except Exception as e:
            logger.error(f"Error in market simulation: {e}")

async def simulate_faction_wars(manager):
    while True:
        await asyncio.sleep(20)  # Check every 20 seconds
        try:
            with get_session() as session:
                # Sum the standing of all characters for each faction
                results = session.exec(
                    select(FactionStanding.faction_id, func.sum(FactionStanding.standing)).group_by(
                        FactionStanding.faction_id
                    )
                ).all()
                for faction_id, total_standing in results:
                    if total_standing > 10.0:
                        # Faction is highly supported globally!
                        # They will launch an offensive and take over a random location
                        target_locs = session.exec(select(Location).where(Location.faction_id != faction_id)).all()
                        if target_locs:
                            target = random.choice(target_locs)
                            target.faction_id = faction_id
                            session.add(target)

                            faction = session.exec(select(Faction).where(Faction.id == faction_id)).first()
                            fact_name = faction.name if faction else faction_id
                            event_msg = f"GLOBAL WAR ALERT: Due to overwhelming player support, the {fact_name} has permanently annexed {target.name}!"

                            # Broadcast to WorldState global_event
                            states = session.exec(select(WorldState)).all()
                            for state in states:
                                state.global_event = event_msg
                                session.add(state)

                            session.commit()

                            # Broadcast immediately
                            await manager.broadcast(json.dumps({"type": "global_event", "event": event_msg}))

                            # Lower standing sum so they don't conquer everything instantly
                            # Reset some players' standings towards this faction
                            standings = session.exec(
                                select(FactionStanding).where(FactionStanding.faction_id == faction_id)
                            ).all()
                            for s in standings:
                                s.standing = s.standing * 0.5
                                session.add(s)
                            session.commit()

        except Exception as e:
            logger.error(f"Error in faction war simulation: {e}")

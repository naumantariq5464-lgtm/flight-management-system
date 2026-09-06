from app.services.waitlist_service import WaitlistService
from app.utils.enums import FareType

def test_waitlist_priority_formula():
    class DummyDB:
        pass
        
    service = WaitlistService(DummyDB())
    
    # Platinum + Flexible = 3000 + 500 = 3500
    p_plat_flex = service._compute_priority_score("PLATINUM", FareType.FLEXIBLE)
    assert p_plat_flex == 3500
    
    # Gold + Basic = 2000 + 0 = 2000
    p_gold_basic = service._compute_priority_score("GOLD", FareType.BASIC_ECONOMY)
    assert p_gold_basic == 2000

    # Standard + Flexible = 0 + 500 = 500
    p_std_flex = service._compute_priority_score("STANDARD", FareType.FLEXIBLE)
    assert p_std_flex == 500

    # Platinum must strictly outrank Gold
    assert p_plat_flex > p_gold_basic

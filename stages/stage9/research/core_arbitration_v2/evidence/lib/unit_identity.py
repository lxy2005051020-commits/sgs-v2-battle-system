from dataclasses import dataclass
import re

@dataclass(frozen=True)
class BattleUnitRef:
    battle_file: str
    camp: str          # 'my' or 'enemy'
    slot: int          # 0, 1, 2
    position: int      # 1, 2, 3 (1=commander, 2=sub1, 3=sub2)
    display_name: str
    hero_type: int | None
    max_troops: int

    @property
    def canonical_id(self) -> str:
        return f"{self.camp}_{self.slot}_{self.display_name}"

    def same_unit(self, other: "BattleUnitRef") -> bool:
        if not isinstance(other, BattleUnitRef):
            return False
        return (self.battle_file == other.battle_file and 
                self.camp == other.camp and 
                self.slot == other.slot and 
                self.display_name == other.display_name)

    def same_camp(self, other: "BattleUnitRef") -> bool:
        if not isinstance(other, BattleUnitRef):
            return False
        return self.camp == other.camp

    def opposing_camp(self, other: "BattleUnitRef") -> bool:
        if not isinstance(other, BattleUnitRef):
            return False
        return self.camp != other.camp

    def __repr__(self) -> str:
        return f"Unit[{self.canonical_id}]"


class UnitRegistry:
    def __init__(self, battle_file: str, lineup: dict):
        self.battle_file = battle_file
        self.units: dict[str, list[BattleUnitRef]] = {'my': [], 'enemy': []}
        self.all_units: list[BattleUnitRef] = []
        self._name_to_units: dict[str, list[BattleUnitRef]] = {}

        for camp in ['my', 'enemy']:
            heroes = lineup.get(camp, [])
            for slot, h in enumerate(heroes):
                name = h.get('name') or 'UNKNOWN_NAME'
                pos = h.get('position') or h.get('pos') or (slot + 1)
                htype = h.get('hero_type') or h.get('root_type')
                max_t = h.get('max_troops') or 0
                ref = BattleUnitRef(
                    battle_file=battle_file,
                    camp=camp,
                    slot=slot,
                    position=pos,
                    display_name=name,
                    hero_type=htype,
                    max_troops=max_t
                )
                self.units[camp].append(ref)
                self.all_units.append(ref)
                self._name_to_units.setdefault(name, []).append(ref)

    def get_unit_by_slot(self, camp: str, slot: int) -> BattleUnitRef | None:
        camp_list = self.units.get(camp, [])
        if 0 <= slot < len(camp_list):
            return camp_list[slot]
        return None

    def has_duplicate_names(self, camp: str) -> bool:
        names = [u.display_name for u in self.units.get(camp, [])]
        return len(names) != len(set(names))

    def resolve_from_event_text(self, text_fragment: str, full_desc_fragment: str | None = None) -> tuple[BattleUnitRef | None, bool]:
        """
        Resolves a unit from text and optional full_desc.
        Returns (BattleUnitRef, is_unambiguous).
        """
        if not text_fragment:
            return None, False

        m_name = re.search(r'\[(.*?)\]', text_fragment)
        name = m_name.group(1) if m_name else text_fragment.strip()

        # Try to detect camp specifically tied to THIS hero name in full_desc_fragment
        detected_camp = None
        if full_desc_fragment:
            # 1. Look for color specifically enclosing this hero name
            m_col = re.search(r"<font color='#([0-9a-fA-F]+)'>\[" + re.escape(name) + r"\]</font>", full_desc_fragment)
            if m_col:
                col = m_col.group(1).lower()
                if col == '75b3ed':
                    detected_camp = 'my'
                elif col == 'ec616b':
                    detected_camp = 'enemy'

            # 2. Look for img tag specifically preceding this hero name
            if not detected_camp:
                m_img = re.search(r"tag_[a-z]+_(my|enemy)\.png'/><font[^>]*>\[" + re.escape(name) + r"\]", full_desc_fragment)
                if m_img:
                    detected_camp = m_img.group(1).lower()

        if detected_camp:
            matches = [u for u in self.units[detected_camp] if u.display_name == name]
            if len(matches) == 1:
                return matches[0], True
            elif len(matches) > 1:
                # Multiple units with identical display name on same camp (e.g. two 勇城卫)
                return matches[0], False
            else:
                return None, False

        # Fallback: check across both camps if display_name is unique in battle
        matches = self._name_to_units.get(name, [])
        if len(matches) == 1:
            return matches[0], True
        elif len(matches) > 1:
            return matches[0], False
        return None, False

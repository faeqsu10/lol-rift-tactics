from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TeamId = Literal["blue", "red"]
TargetType = Literal["enemy", "self", "all-enemies"]
Role = Literal["Vanguard", "Mage", "Marksman"]
EffectKind = Literal["damage", "shield", "stun"]


@dataclass(frozen=True)
class AbilityEffect:
    kind: EffectKind
    amount: int = 0
    turns: int = 0


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    description: str
    cooldown: int
    target_type: TargetType
    effects: tuple[AbilityEffect, ...]


@dataclass(frozen=True)
class ChampionBlueprint:
    id: str
    name: str
    title: str
    role: Role
    team: TeamId
    max_hp: int
    speed: int
    accent: str
    abilities: tuple[Ability, ...]


BLUE_TEAM: tuple[ChampionBlueprint, ...] = (
    ChampionBlueprint(
        id="blue-garen",
        name="가렌",
        title="데마시아의 힘",
        role="Vanguard",
        team="blue",
        max_hp=98,
        speed=55,
        accent="#d6b35f",
        abilities=(
            Ability(
                id="decisive-strike",
                name="결정타",
                description="전방으로 돌진해 강한 참격을 가합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=18),),
            ),
            Ability(
                id="courage",
                name="용기",
                description="몸을 낮추고 단단한 보호막을 얻습니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=22),),
            ),
            Ability(
                id="judgment",
                name="심판",
                description="회전하면서 적 전체를 휩씁니다.",
                cooldown=3,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=12),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-ahri",
        name="아리",
        title="구미호",
        role="Mage",
        team="blue",
        max_hp=78,
        speed=68,
        accent="#ec8d8d",
        abilities=(
            Ability(
                id="orb-of-deception",
                name="현혹의 구슬",
                description="마력을 담은 구슬을 발사합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=17),),
            ),
            Ability(
                id="charm",
                name="매혹",
                description="적을 끌어당기며 기절시킵니다.",
                cooldown=3,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=10),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="spirit-rush",
                name="혼령 질주",
                description="빠르게 파고들며 강한 마법 피해를 줍니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=25),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-jinx",
        name="징크스",
        title="난폭한 말괄량이",
        role="Marksman",
        team="blue",
        max_hp=74,
        speed=72,
        accent="#6dd7d0",
        abilities=(
            Ability(
                id="zap",
                name="빠직!",
                description="장거리 전격 사격으로 적을 꿰뚫습니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=15),),
            ),
            Ability(
                id="flame-chompers",
                name="와작와작 뻥!",
                description="덫을 던져 적을 폭발과 함께 묶습니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=8),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="super-mega-death-rocket",
                name="초강력 초토화 로켓!",
                description="적 전열 전체를 뒤흔드는 거대 로켓을 발사합니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=14),),
            ),
        ),
    ),
)


RED_TEAM: tuple[ChampionBlueprint, ...] = (
    ChampionBlueprint(
        id="red-darius",
        name="다리우스",
        title="녹서스의 실력자",
        role="Vanguard",
        team="red",
        max_hp=102,
        speed=52,
        accent="#d97d59",
        abilities=(
            Ability(
                id="crippling-strike",
                name="마비의 일격",
                description="도끼를 크게 휘둘러 내려칩니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=18),),
            ),
            Ability(
                id="defy",
                name="응수",
                description="몸을 굳혀 보호막을 형성합니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=20),),
            ),
            Ability(
                id="noxian-guillotine",
                name="녹서스의 단두대",
                description="약한 적을 마무리하는 처형 일격입니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=28),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-annie",
        name="애니",
        title="어둠의 아이",
        role="Mage",
        team="red",
        max_hp=76,
        speed=66,
        accent="#f0b35f",
        abilities=(
            Ability(
                id="disintegrate",
                name="붕괴",
                description="작은 불꽃을 압축해 발사합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=16),),
            ),
            Ability(
                id="molten-shield",
                name="용암 방패",
                description="몸을 감싸는 화염 보호막을 만듭니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=18),),
            ),
            Ability(
                id="summon-tibbers",
                name="티버 소환",
                description="거대한 폭발로 적 전체를 불태웁니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=13),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-caitlyn",
        name="케이틀린",
        title="필트오버의 보안관",
        role="Marksman",
        team="red",
        max_hp=72,
        speed=70,
        accent="#9ab3e6",
        abilities=(
            Ability(
                id="piltover-peacemaker",
                name="필트오버 피스메이커",
                description="정밀한 라이플 사격을 가합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=18),),
            ),
            Ability(
                id="yordle-snap-trap",
                name="요들잡이 덫",
                description="적을 묶어 둔 뒤 폭발시킵니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=9),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="ace-in-the-hole",
                name="비장의 한 발",
                description="집중 사격으로 적 하나를 꿰뚫습니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=25),),
            ),
        ),
    ),
)


ALL_BLUEPRINTS: tuple[ChampionBlueprint, ...] = (*BLUE_TEAM, *RED_TEAM)

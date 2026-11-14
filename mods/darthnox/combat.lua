-- SPDX-License-Identifier: MIT
-- DarthNox — the parry (D J A). While he is in his guard frames, the first hit
-- that would land on him is cancelled and he jumps straight into the counter:
-- a huge unblockable stab that leaves the victim dizzy (darthnox.txt 245-248).
-- Only the guard frames do this; the counter itself has no hurtbox.
--
-- Also Mathilde's tornado (object 65): it lifts each fighter once (for its ~1 s
-- life) and its landing damage is halved.
--
-- Also Mathilde's launcher strike (A during a vault, mathilde.txt 301/296):
-- it launches a grounded target, but one already in the air only gets a small
-- pop, so it starts a juggle instead of sending them sky-high.
--
-- Also our projectiles are tougher than a stock ball (DarthNox's crescent 62,
-- Mathilde's homing staff 64), between a normal ball and Henry's piercing
-- arrow: each shrugs off the first TOUGHNESS opponents that would break it (a
-- clashing ball, a punch, a weapon) and keeps flying, breaking a clashing
-- ball as it goes. The next one breaks it as usual. Piercing and vanishing
-- balls (states 3006/3005, e.g. Henry's arrow) still beat it outright.

return function(base)
    local fighter_id = 61
    local TORNADO = 65   -- Mathilde's D^J tornado object
    local MATHILDE, LAUNCHERS, LOW_POP = 63, {[301] = true, [296] = true}, -5.0
    local parry_first, parry_last, counter_frame = 241, 243, 245
    local PARRY_HEAL = 50
    local objects = require("base/game/objects")
    local kinds = require("base/game/constants").attack_kinds
    local parryable = {[kinds.plain] = true, [kinds.thrown_body] = true, [kinds.held_item] = true}
    local COD1EH, ROPE_FIRST, ROPE_LAST, REEL_FRAME = 68, 271, 274, 277
    local TOUGH = {[62] = 1, [64] = 1}   -- projectile id -> opponents it shrugs off
    local states = require("base/game/constants").frame_states
    local FLYING, STRONG = states.flying_ball, {[states.vanishing_ball] = true, [states.flying_missile] = true}

    local function state_of(value) return value.record.frame(value.frame).state end

    -- true while `ball` can still shrug off `other` (the same opponent counts once)
    local function shrugs(ball, other)
        if not TOUGH[ball.record.id] or state_of(ball) ~= FLYING or STRONG[state_of(other)] then return false end
        ball.dod_beaten = ball.dod_beaten or {}
        if ball.dod_beaten[other] then return true end
        local count = 0
        for _ in pairs(ball.dod_beaten) do count = count + 1 end
        if count >= TOUGH[ball.record.id] then return false end
        ball.dod_beaten[other] = true
        return true
    end
    local apply = base.apply

    function base.apply(state, p)
        local attacker = state.items[p]
        if attacker then
            local frame = attacker.record.frame(attacker.frame_at_pass)
            for position = 1, attacker.hit_list_count do
                local itr = frame.interactions[attacker.hit_list_itr[position]]
                local victim = objects.lookup(state, attacker.hit_list[position])
                -- plain hits, thrown bodies and weapon swings; grabs can't be parried
                if itr and parryable[itr.kind] and victim and victim.record.id == fighter_id
                   and victim.frame >= parry_first and victim.frame <= parry_last
                   and (victim.pair_rest[p] or 0) <= 0 then
                    victim.pair_rest[p] = 20          -- this attacker's hit is void
                    victim.frame = counter_frame
                    -- a successful parry restores PARRY_HEAL hp (up to his max)
                    victim.hp = math.min(victim.max_hp, victim.hp + PARRY_HEAL)
                    if victim.dark_hp < victim.hp then victim.dark_hp = victim.hp end
                    victim.facing = attacker.x < victim.x and 1 or 0
                    attacker.hit_lag = 6              -- a beat of freeze sells the parry
                end
            end
        end
        -- Something hitting one of our tough projectiles: void it while it has toughness left.
        if attacker then
            for position = 1, attacker.hit_list_count do
                local victim = objects.lookup(state, attacker.hit_list[position])
                if victim and (victim.pair_rest[p] or 0) <= 0 and shrugs(victim, attacker) then
                    victim.pair_rest[p] = 20
                end
            end
        end
        -- One of our tough projectiles hitting another ball: it breaks that ball
        -- and, while it has toughness left, keeps flying (the engine would stop it).
        local keep
        if attacker and TOUGH[attacker.record.id] and state_of(attacker) == FLYING then
            local balls_only, any = true, false
            for position = 1, attacker.hit_list_count do
                local victim = objects.lookup(state, attacker.hit_list[position])
                if victim and (victim.pair_rest[p] or 0) <= 0 then
                    any = true
                    if victim.record.kind ~= attacker.record.kind or not shrugs(attacker, victim) then balls_only = false end
                end
            end
            if any and balls_only then
                keep = {frame = attacker.frame, wait = attacker.wait_counter, vx = attacker.vx, vy = attacker.vy, vz = attacker.vz}
            end
        end
        local tornado = attacker and attacker.record.id == TORNADO
        if tornado then
            -- A fighter this tornado already lifted and dropped isn't caught again
            -- (it drifts forward and would re-lift them after every bounce).
            for position = 1, attacker.hit_list_count do
                local victim = objects.lookup(state, attacker.hit_list[position])
                if victim then
                    -- keyed to this tornado object, not its slot (slots are reused)
                    if victim.y_int < -5 then victim.dod_tornado = attacker
                    elseif victim.dod_tornado == attacker then victim.pair_rest[p] = 99 end
                end
            end
        end
        local launcher = attacker and attacker.record.id == MATHILDE and LAUNCHERS[attacker.frame_at_pass]
        local airborne = {}
        if launcher then
            for position = 1, attacker.hit_list_count do
                local victim = objects.lookup(state, attacker.hit_list[position])
                if victim and victim.y_int < 0 then airborne[victim] = true end
            end
        end
        -- Cod1eh's DvA rope blade: whoever it hurts is reeled in (physics.lua).
        local rope = attacker and attacker.record.id == COD1EH and attacker.frame_at_pass >= ROPE_FIRST
            and attacker.frame_at_pass <= ROPE_LAST
        local hp_before = {}
        if rope then
            for position = 1, attacker.hit_list_count do
                local victim = objects.lookup(state, attacker.hit_list[position])
                if victim and victim.record.kind == 0 then hp_before[victim] = victim.hp end
            end
        end
        local result = apply(state, p)
        if rope then
            for victim, hp in pairs(hp_before) do
                local s = state_of(victim)
                if victim.hp < hp and s ~= states.defending and s ~= states.broken_defend and not attacker.dod_reel then
                    victim.dod_pull = {by = attacker}
                    attacker.dod_reel = victim
                    attacker.frame, attacker.wait_counter = REEL_FRAME, 0   -- he holds the pull
                end
            end
        end
        if keep and attacker.frame ~= keep.frame then
            attacker.frame, attacker.wait_counter = keep.frame, keep.wait
            attacker.vx, attacker.vy, attacker.vz = keep.vx, keep.vy, keep.vz
        end
        if launcher then
            for victim in pairs(airborne) do
                -- the hit set its upward impulse (-13); an airborne target pops low
                if victim.impulse_y < LOW_POP then victim.impulse_y = LOW_POP end
            end
        end
        if tornado then
            -- Half the whirlwind's usual landing damage (20 -> 10).
            for position = 1, attacker.hit_list_count do
                local victim = objects.lookup(state, attacker.hit_list[position])
                if victim and victim.fall_damage == -20 then victim.fall_damage = -10 end
            end
        end
        return result
    end

    return base
end

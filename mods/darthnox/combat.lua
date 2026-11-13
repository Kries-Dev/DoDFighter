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

return function(base)
    local fighter_id = 61
    local TORNADO = 65   -- Mathilde's D^J tornado object
    local MATHILDE, LAUNCHERS, LOW_POP = 63, {[301] = true, [296] = true}, -5.0
    local parry_first, parry_last, counter_frame = 241, 243, 245
    local objects = require("base/game/objects")
    local kinds = require("base/game/constants").attack_kinds
    local parryable = {[kinds.plain] = true, [kinds.thrown_body] = true, [kinds.held_item] = true}
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
                    victim.facing = attacker.x < victim.x and 1 or 0
                    attacker.hit_lag = 6              -- a beat of freeze sells the parry
                end
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
        local result = apply(state, p)
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

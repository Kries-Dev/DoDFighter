-- SPDX-License-Identifier: MIT
-- DarthNox — the parry (D J A). While he is in his guard frames, the first hit
-- that would land on him is cancelled and he jumps straight into the counter:
-- a huge unblockable stab that leaves the victim dizzy (darthnox.txt 245-248).
-- Only the guard frames do this; the counter itself has no hurtbox.

return function(base)
    local fighter_id = 61
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
        return apply(state, p)
    end

    return base
end

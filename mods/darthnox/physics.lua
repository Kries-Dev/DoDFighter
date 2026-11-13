-- SPDX-License-Identifier: MIT
-- DoD Fighter — moves that keep going through a landing.
--
-- When anything airborne touches the ground the engine switches it to the
-- landing crouch (physics.lua landed(): crouch2, 219) unless it is falling or
-- burning. Mathilde's DvA combo starts during her vault, in the air; without
-- this it would be cut off the moment she lands. Frames listed here stay
-- where they are on landing (now on the ground) instead.

local KEEP_ON_LANDING = {
    [63] = {{270, 281}, {300, 305}},   -- Mathilde: the staff combo; the air carry's rise
}
local CROUCH_ALTERNATE = 219

-- Mathilde's air carry: while she rises (301-305) the fighter her strikes
-- knocked down (combat.lua marks them) is held just in front of her at her
-- height and speed, so they go up together; the slam (306) then hits them.
local MATHILDE, CARRY_FIRST, CARRY_LAST, CARRY_REACH = 63, 301, 305, 38
local FACING_RIGHT = 0

-- Starting the carry (300) clears her hit rest on everyone: the stab she
-- vaulted from leaves a 20-tick rest that would void an early first strike.
local CARRY_START = 300
local function fresh_start(match, value)
    if value.frame ~= CARRY_START then value.dod_fresh = nil return end
    if value.dod_fresh then return end
    value.dod_fresh = true
    local slot
    for k, item in pairs(match.items) do if item == value then slot = k end end
    if slot == nil then return end
    for _, item in pairs(match.items) do
        if item ~= value and item.pair_rest then item.pair_rest[slot] = 0 end
    end
end

local function carry(value)
    local victim = value.dod_carry
    if not victim then return end
    if value.frame < CARRY_FIRST or value.frame > CARRY_LAST or victim.hp <= 0
       or victim.frame < 180 or victim.frame > 191 then
        value.dod_carry = nil
        return
    end
    local x = value.x + (value.facing == FACING_RIGHT and CARRY_REACH or -CARRY_REACH)
    victim.x, victim.x_int = x, math.floor(x)
    victim.y, victim.y_int = value.y, value.y_int
    victim.z, victim.z_int = value.z, value.z_int
    victim.vx, victim.vy, victim.vz = value.vx, value.vy, 0
end

return function(base)
    local step = base.step

    function base.step(match, value)
        local keep = KEEP_ON_LANDING[value.record.id]
        local before = value.frame
        local result = step(match, value)
        if value.record.id == MATHILDE then fresh_start(match, value); carry(value) end
        if keep and value.frame == CROUCH_ALTERNATE then
            for _, range in ipairs(keep) do
                if before >= range[1] and before <= range[2] then value.frame = before end
            end
        end
        return result
    end

    return base
end

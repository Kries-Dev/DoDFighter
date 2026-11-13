-- SPDX-License-Identifier: MIT
-- DoD Fighter — moves that keep going through a landing.
--
-- When anything airborne touches the ground the engine switches it to the
-- landing crouch (physics.lua landed(): crouch2, 219) unless it is falling or
-- burning. Mathilde's DvA combo starts during her vault, in the air; without
-- this it would be cut off the moment she lands. Frames listed here stay
-- where they are on landing (now on the ground) instead.

local KEEP_ON_LANDING = {
    [63] = {{270, 281}, {300, 303}, {295, 298}},   -- Mathilde: the staff combo; the launcher strikes
}
local CROUCH_ALTERNATE = 219

-- Mathilde's launcher strikes (300, 295) and her DJA air extension (320) clear
-- her hit rest on everyone when they start: the stab she went up from leaves a
-- 20-tick rest that would void an early hit.
local MATHILDE, STRIKE_START = 63, {[300] = true, [295] = true, [320] = true}

local function fresh_start(match, value)
    if not STRIKE_START[value.frame] then value.dod_fresh = nil return end
    if value.dod_fresh == value.frame then return end
    value.dod_fresh = value.frame
    local slot
    for k, item in pairs(match.items) do if item == value then slot = k end end
    if slot == nil then return end
    for _, item in pairs(match.items) do
        if item ~= value and item.pair_rest then item.pair_rest[slot] = 0 end
    end
end

return function(base)
    local step = base.step

    function base.step(match, value)
        local keep = KEEP_ON_LANDING[value.record.id]
        local before = value.frame
        local result = step(match, value)
        if value.record.id == MATHILDE then fresh_start(match, value) end
        if keep and value.frame == CROUCH_ALTERNATE then
            for _, range in ipairs(keep) do
                if before >= range[1] and before <= range[2] then value.frame = before end
            end
        end
        return result
    end

    return base
end

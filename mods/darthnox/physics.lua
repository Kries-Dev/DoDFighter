-- SPDX-License-Identifier: MIT
-- DoD Fighter — moves that keep going through a landing.
--
-- When anything airborne touches the ground the engine switches it to the
-- landing crouch (physics.lua landed(): crouch2, 219) unless it is falling or
-- burning. Mathilde's DvA combo starts during her vault, in the air; without
-- this it would be cut off the moment she lands. Frames listed here stay
-- where they are on landing (now on the ground) instead.

local KEEP_ON_LANDING = {
    [63] = {first = 270, last = 281},   -- Mathilde: the staff combo after the vault
}
local CROUCH_ALTERNATE = 219

return function(base)
    local step = base.step

    function base.step(match, value)
        local keep = KEEP_ON_LANDING[value.record.id]
        local before = value.frame
        local result = step(match, value)
        if keep and before >= keep.first and before <= keep.last and value.frame == CROUCH_ALTERNATE then
            value.frame = before
        end
        return result
    end

    return base
end

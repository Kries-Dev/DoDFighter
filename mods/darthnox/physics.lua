-- SPDX-License-Identifier: MIT
-- DoD Fighter — moves that keep going through a landing, and Cod1eh's
-- teleport, smoke slow and rope pull.
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

-- Cod1eh (68): his Izuna drop (284-287, in the air) turns into the slam (288)
-- on landing; DvJ teleports him behind the nearest enemy on entering 264; his
-- D^J smoke (object 70, frames below 24) slows enemies inside it; a DvA rope
-- hit (combat.lua sets dod_pull) reels the target in to his feet.
local COD1EH, SMOKE, TELEPORT_FRAME = 68, 70, 264
local LAND_TO = {[68] = {[284] = 288, [285] = 288, [286] = 288, [287] = 288}}
local SMOKE_REACH_X, SMOKE_REACH_Z, SMOKE_LAST_FRAME = 70, 28, 23
local SLOW_TICKS, SLOW_FACTOR = 15, 0.45     -- slowed while inside and half a second after
local BEHIND = 48                            -- teleport: this far behind the target
local CHARACTER = 0

local function trunc(x) return x >= 0 and math.floor(x) or math.ceil(x) end

local function in_smoke(match, value)
    for _, item in pairs(match.items) do
        if item and item.record.id == SMOKE and item.frame <= SMOKE_LAST_FRAME and item.team ~= value.team
           and math.abs(item.x - value.x) < SMOKE_REACH_X and math.abs(item.z - value.z) < SMOKE_REACH_Z then
            return true
        end
    end
    return false
end

local function teleport(match, value)
    local best, best_d
    for _, item in pairs(match.items) do
        if item and item ~= value and item.record.kind == CHARACTER and item.hp > 0 and item.team ~= value.team then
            local d = math.abs(item.x - value.x) + math.abs(item.z - value.z)
            if not best_d or d < best_d then best, best_d = item, d end
        end
    end
    if not best then return end
    local side = best.facing == 0 and -1 or 1              -- behind = opposite the way they face
    value.x, value.z, value.y = best.x + side * BEHIND, best.z, 0
    value.vx, value.vy, value.vz = 0, 0, 0
    value.facing = side < 0 and 0 or 1                     -- face them
    value.x_int, value.z_int, value.y_int = trunc(value.x), trunc(value.z), 0
end

local function reel(value)
    local pull, by = value.dod_pull, value.dod_pull.by
    local goal = by.x + (by.facing == 0 and 50 or -50)
    value.x = value.x + (goal - value.x) / pull.ticks
    value.z = value.z + (by.z - value.z) / pull.ticks
    value.vx, value.vz = 0, 0
    value.x_int, value.z_int = trunc(value.x), trunc(value.z)
    pull.ticks = pull.ticks - 1
    if pull.ticks <= 0 or by.hp <= 0 then value.dod_pull = nil end
end

return function(base)
    local step = base.step

    function base.step(match, value)
        local keep = KEEP_ON_LANDING[value.record.id]
        local before = value.frame
        local x0, z0 = value.x, value.z
        local result = step(match, value)
        if value.record.kind == CHARACTER then
            if in_smoke(match, value) then value.dod_slow = SLOW_TICKS end
            if (value.dod_slow or 0) > 0 then
                value.dod_slow = value.dod_slow - 1
                value.x = x0 + (value.x - x0) * SLOW_FACTOR
                value.z = z0 + (value.z - z0) * SLOW_FACTOR
                value.x_int, value.z_int = trunc(value.x), trunc(value.z)
            end
            if value.dod_pull then reel(value) end
        end
        if value.record.id == COD1EH then
            if value.frame == TELEPORT_FRAME then
                if not value.dod_teleported then teleport(match, value); value.dod_teleported = true end
            else
                value.dod_teleported = nil
            end
        end
        local land = LAND_TO[value.record.id]
        if land and value.frame == CROUCH_ALTERNATE and land[before] then value.frame = land[before] end
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

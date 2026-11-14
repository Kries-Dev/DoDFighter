-- SPDX-License-Identifier: MIT
-- DoD Fighter — our fighters' sprites and authored frames over a stock fighter's
-- mechanics (DarthNox over Deep, Mathilde over Davis, Cod1eh over Rudolf; see FIGHTERS below).
--
-- The art set is incomplete (8 cells: idle + walk). Rather than block on
-- drawing ~200 more frames, this inherits a base fighter's full frame table —
-- states, itr/bdy boxes, next-wiring, catches, falls — and overrides only what
-- we actually have:
--
--   * frames we authored in darthnox.txt  -> our picture
--   * every other frame                   -> IDLE_PICTURE as a placeholder
--   * all frames                          -> our centres and our sheets
--
-- The character is therefore fully playable from day one; unauthored actions
-- read as a held pose rather than a missing sprite. Replace frames in
-- darthnox.txt as the art lands and they stop falling back automatically.
--
-- Two ways an authored frame goes further than a picture swap:
--   * it has a bdy: or itr:, or its name differs from Deep's frame at that
--     number           -> it replaces Deep's frame whole (his own mechanics: the
--                         special moves; the name rule covers invincible frames
--                         that have neither box)
--   * it has any hit_*:  -> its hit_* fields replace Deep's (his own inputs)

local IDLE_PICTURE = 0
-- DarthNox fights with a sword: frames he keeps from Deep that play LF2's punch
-- sounds (007: dash attack, grab throw; 014: hitting a held opponent) play the
-- weapon swish instead. Mathilde keeps the punch sounds.
local SWORD_SOUNDS = {["data\\007.wav"] = "data\\008.wav", ["data\\014.wav"] = "data\\008.wav"}

-- Our fighters and the stock fighter each one inherits its mechanics from.
local FIGHTERS = {
    ["mods/darthnox/darthnox.txt"] = {base = 1, sounds = SWORD_SOUNDS},   -- DarthNox over Deep
    ["mods/darthnox/mathilde.txt"] = {base = 11},   -- Mathilde over Davis
    -- Cod1eh over Rudolf: Rudolf's A already throws shurikens. own_inputs: his
    -- standing/walking/defend frames replace Rudolf's special-move inputs even
    -- where they are all 0, so he doesn't inherit transform, vanish or clone.
    ["mods/darthnox/cod1eh.txt"] = {base = 5, sounds = SWORD_SOUNDS, own_inputs = true},
}
local INPUT_STATES = {[0] = true, [1] = true, [7] = true}   -- standing, walking, defend

-- Stock fighters with restyled sheets: their data stays stock, only the listed
-- sheets (by position in the file: 1 = pictures 0-69) come from the mod.
local RESTYLED = {
    -- the user's black-and-white Bandit, both sheets drawn by the user (art/bandit_0_edit.webp,
    -- art/bandit_1_edit.webp: hurt, run/dash attacks, weapon moves, fire/ice), via tools/import_sheet.py
    ["data/bandit.dat"] = {[1] = "mods/darthnox/bandit_0.bmp", [2] = "mods/darthnox/bandit_1.bmp"},
}

local function restyle(data, sheets)
    for index, resource in pairs(sheets) do
        local sheet = data.sheets and data.sheets[index]
        if sheet then sheet.resource, sheet.path = resource, resource:gsub("/", "\\") end
    end
    return data
end

return function(base)
    local load = base.load
    local cache = {}

    function base.load(path)
        if RESTYLED[path] then return restyle(load(path), RESTYLED[path]) end
        local fighter = FIGHTERS[path]
        if not fighter then return load(path) end
        if cache[path] then return cache[path] end

        local source = require("base/game/catalog").objects().by_id[fighter.base]
        assert(source, path .. " needs base fighter " .. fighter.base .. " for its mechanics")

        local original = load(source.path)
        local authored = load(path)

        local copy = {}
        cache[path] = copy
        for key, value in pairs(original) do copy[key] = value end
        copy.name = authored.name:gsub("_", " ")
        copy.head, copy.small = authored.head, authored.small
        copy.sheets = authored.sheets

        copy.movement = {}
        for key, value in pairs(original.movement) do copy.movement[key] = value end
        for key, value in pairs(authored.movement) do
            if value and value ~= 0 then copy.movement[key] = value end
        end

        -- Centres come from the slicer's registration, so every frame sits on
        -- the same root. One pair for now; per-frame once the art is authored.
        -- (Frame 0, standing, is always authored; undefined frames read as 0,0.)
        local center_x, center_y = authored.frames[0].center_x, authored.frames[0].center_y
        assert(authored.frames[0].name ~= "" and center_x > 0, "darthnox.txt needs frame 0 with its centre")

        -- Deep's boxes and points are measured from Deep's picture origin; our
        -- pictures put the feet at (center_x, center_y) instead. Moving every
        -- coordinate by the difference of the centres keeps each box where it
        -- was relative to the feet (combat, weapons and spawns all work from
        -- x - center_x). Without this every inherited hitbox sat ~34 px behind him.
        local function shifted(area, dx, dy)
            local moved = {}
            for key, value in pairs(area) do moved[key] = value end
            moved.x, moved.y = (area.x or 0) + dx, (area.y or 0) + dy
            return moved
        end
        local function rebase(own, frame)
            local dx, dy = center_x - frame.center_x, center_y - frame.center_y
            if dx == 0 and dy == 0 then return end
            local interactions, bodies = {}, {}
            for i, area in ipairs(frame.interactions) do interactions[i] = shifted(area, dx, dy) end
            for i, area in ipairs(frame.bodies) do bodies[i] = shifted(area, dx, dy) end
            own.interactions, own.bodies = interactions, bodies
            own.interaction_bounds = shifted(frame.interaction_bounds, dx, dy)
            own.body_bounds = shifted(frame.body_bounds, dx, dy)
            for _, point in ipairs({"opoint", "wpoint", "cpoint", "bpoint"}) do
                if frame[point] then own[point] = shifted(frame[point], dx, dy) end
            end
        end

        local function authored_frame(index)
            local mine = authored.frames[index]
            if mine and mine.name ~= "" then return mine end
        end
        local function has_hits(frame)
            for _, value in pairs(frame.hits) do
                if value ~= 0 then return true end
            end
            return false
        end

        copy.frames = {}
        for index, frame in pairs(original.frames) do
            local mine = authored_frame(index)
            local own = {}
            if mine and (#mine.bodies > 0 or #mine.interactions > 0 or mine.name ~= frame.name) then
                for key, value in pairs(mine) do own[key] = value end
            else
                for key, value in pairs(frame) do own[key] = value end
                rebase(own, frame)
                local swap = fighter.sounds
                if swap and own.sound and swap[own.sound:lower()] then own.sound = swap[own.sound:lower()] end
                own.picture = (mine and mine.picture) or IDLE_PICTURE
                if mine and (has_hits(mine) or (fighter.own_inputs and INPUT_STATES[frame.state])) then
                    own.hits = mine.hits
                end
            end
            if center_x then own.center_x, own.center_y = center_x, center_y end
            copy.frames[index] = own
        end
        -- Frames Deep doesn't have at all come straight from darthnox.txt.
        for index, mine in pairs(authored.frames) do
            if not copy.frames[index] and mine.name ~= "" then copy.frames[index] = mine end
        end

        return copy
    end

    return base
end

-- SPDX-License-Identifier: MIT
-- DarthNox — our sprites and authored frames over a base fighter's mechanics.
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

return function(base)
    local load = base.load
    local fighter_path = "mods/darthnox/darthnox.txt"
    local copy

    function base.load(path)
        if path ~= fighter_path then return load(path) end
        if copy then return copy end

        local source
        for _, fighter in ipairs(require("base/game/catalog").load()) do
            if fighter.id >= 1 and fighter.id < 30 then source = fighter; break end
        end
        assert(source, "darthnox needs a base fighter for its mechanics")

        local original = load(source.path)
        local authored = load(path)

        copy = {}
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
        local center_x, center_y
        for _, frame in pairs(authored.frames) do
            if frame.defined ~= false then
                center_x, center_y = frame.center_x, frame.center_y
                break
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
                own.picture = (mine and mine.picture) or IDLE_PICTURE
                if mine and has_hits(mine) then own.hits = mine.hits end
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

-- SPDX-License-Identifier: MIT
-- DarthNox — our sprites and authored frames over a base fighter's mechanics.
--
-- The art set is incomplete (4 cells: a walk cycle). Rather than block on
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

local IDLE_PICTURE = 3

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

        copy.frames = {}
        for index, frame in pairs(original.frames) do
            local own = {}
            for key, value in pairs(frame) do own[key] = value end
            local mine = authored.frames[index]
            own.picture = (mine and mine.picture) or IDLE_PICTURE
            if center_x then own.center_x, own.center_y = center_x, center_y end
            copy.frames[index] = own
        end

        return copy
    end

    return base
end

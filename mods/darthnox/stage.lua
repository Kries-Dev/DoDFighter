-- SPDX-License-Identifier: MIT
-- DoD Fighter — stage mode on our own stages. The waves, scroll bounds and
-- music are in our stage file (mods/darthnox/stage.txt, read by stage_mode.lua);
-- this picks the background each sub-stage is fought on (STAGES, by run id:
-- 0 = 1-1 ... 4 = 1-5). The engine keeps one background per stage group, so
-- match.lua starts a run on ours and a change between sub-stages (1-4 -> 1-5)
-- is swapped in here, with the fighters moved onto the new floor.
-- Stage file bounds must fit the stage: a sub-stage's last bound is its right
-- wall (camera.lua), since players have to reach it to go on.

local BG = "mods/darthnox/bg/"
local ROOF, ROOF_NIGHT = BG .. "roof.txt", BG .. "roofn.txt"
local STAGES = {
    -- stage 1 (1-1 and 1-2 keep LF2's background until their paintings come)
    [2] = BG .. "cells.txt",    -- 1-3: Cell Block
    [3] = BG .. "barr.txt",     -- 1-4: Barracks
    [4] = BG .. "hall.txt",     -- 1-5: Throne Hall
    -- stage 2: the city
    [10] = ROOF, [11] = ROOF, [12] = ROOF, [13] = ROOF,   -- 2-1 .. 2-4: Sunset Rooftop
    [14] = ROOF_NIGHT,                                    -- 2-5: Rooftop at Night
}
-- Keep in step with tools/stage_layout.py (LAYOUT), which scales each sub-stage's
-- bounds to the stage named here.

return function(base)
    local background = require("base/game/background")
    local constants = require("base/game/constants")
    local record_kinds = constants.record_kinds

    -- the background a stage-mode run id is fought on (nil = the engine's own)
    function base.dod_background(id) return STAGES[id] end

    local update = base.update
    function base.update(state, run)
        local before = run.id
        local display = update(state, run)
        local path = run.id ~= before and STAGES[run.id]
        if path then
            local stage = background.load(path)
            if state.stage ~= stage then
                state.stage = stage
                state.view = background.create_state(stage)
                local near, far = stage.zboundary[1] or 0, stage.zboundary[2] or 0
                for index = 0, constants.item_slots - 1 do
                    local value = state.items[index]
                    if value and value.record.kind == record_kinds.character then
                        value.z_int = engine.random(far - near) + near
                        value.z = value.z_int
                    end
                end
            end
        end
        return display
    end

    return base
end

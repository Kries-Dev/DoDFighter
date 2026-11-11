-- SPDX-License-Identifier: MIT
-- DarthNox — Urban Bridge's side walls. The engine stops fighters only at x 0
-- and the stage width (794), where half the sprite is off-screen and standing
-- on the concrete barriers; on this stage they stop 60 px in from each side.

return function(base)
    local stage_path = "mods/darthnox/bg/bridge.txt"
    local left, right = 60, 734
    local background = require("base/game/background")
    local record_kinds = require("base/game/constants").record_kinds
    local step = base.step

    function base.step(state)
        if state.stage == background.load(stage_path) then
            for index = 0, 19 do
                local value = state.items[index]
                if value and value.record.kind == record_kinds.character then
                    if value.x < left then value.x = left end
                    if value.x > right then value.x = right end
                end
            end
        end
        return step(state)
    end

    return base
end

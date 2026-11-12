-- SPDX-License-Identifier: MIT
-- DarthNox — no menu music by default. Every menu (title, character select,
-- options) plays bgm/main.wma; it is skipped and whatever was playing stops.
-- Match and stage music are unchanged. Set MENU_MUSIC = true to bring it back.

local MENU_MUSIC = false
local MENU_TRACK = "bgm/main.wma"

return function(base)
    local play = base.play
    function base.play(path)
        if not MENU_MUSIC and (path:gsub("\\", "/"):lower()) == MENU_TRACK then
            base.stop()
            return
        end
        return play(path)
    end
    return base
end

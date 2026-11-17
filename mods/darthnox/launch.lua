-- SPDX-License-Identifier: MIT
-- DoD Fighter — the launch screen without LF2's leftovers: no credit lines
-- (bottom right), no version label (top right) and no "official website" entry.
--
-- The menu picture is drawn without the website line (the sheet stays whole: the
-- "options" entry is spelled from its letters) and "options" moves up into that
-- row. Input follows: on the launch menu, the pointer in the website row is
-- handed to the base code as if it were on the options row, and the old options
-- row is dead; keyboard focus skips the old options stop, so its website stop now
-- means options. Website links do nothing.

local WEBSITES = {open_website = true, open_original_website = true,
    open_marti_website = true, open_starsky_website = true}
local TOP = 0xca                                   -- launch.lua's menu top
local WEBSITE = {TOP + 0x89, TOP + 0xa2}           -- its rows (pointer y ranges)
local OPTIONS = {TOP + 0xa7, TOP + 0xc0}
local SHIFT = OPTIONS[1] - WEBSITE[1]              -- options drawn this much higher

return function(base)
    local navigation = require("base/ui/navigation")
    local create, update = base.create, base.update

    function base.create(options)
        local state = create(options)
        state.credits = {}
        return state
    end

    local function remap(view)
        local y = view.pointer_y
        if y and y >= WEBSITE[1] and y <= WEBSITE[2] then view.pointer_y = y + SHIFT
        elseif y and y >= OPTIONS[1] and y <= OPTIONS[2] then view.pointer_y = 0 end
    end

    function base.update(state, flow_input, context)
        local proxy = {}
        for key, value in pairs(context) do proxy[key] = value end
        function proxy.action(name, ...)
            if WEBSITES[name] then return end
            return context.action(name, ...)
        end
        -- the menu's input, while the base update runs
        local apply = navigation.apply
        navigation.apply = function(nav, input, spec)
            if spec.page ~= "menu" then return apply(nav, input, spec) end
            local targets = {}
            for index, target in ipairs(spec.targets) do
                if index ~= 6 then targets[#targets + 1] = target end   -- 6: the old options stop
            end
            local copy = {}
            for key, value in pairs(spec) do copy[key] = value end
            copy.targets = targets
            local view = apply(nav, input, copy)
            remap(view)
            return view
        end
        local ok, result = pcall(update, state, flow_input, proxy)
        navigation.apply = apply
        if not ok then error(result, 0) end

        local kept = {}
        for _, command in ipairs(state.display) do
            local sheet = command[1] == "sprite" and command[2] == "pe/menu_clip5"
            local rect = sheet and command[3]
            if command[1] == "image" and command[2] == "pe/lf2_cursor" and flow_input.pointer_y then
                -- the cursor where the pointer really is (the menu saw a moved one)
                local copy = {}
                for key, value in pairs(command) do copy[key] = value end
                copy[4] = math.min(flow_input.pointer_y + 2, 0x217)
                kept[#kept + 1] = copy
            elseif command[1] == "text" and command[2] == engine.build_label then
                -- the version label: dropped
            elseif rect and rect[1] == 285 and rect[2] == 32 then
                -- the highlighted "official website": dropped
            elseif rect and rect[1] == 0 and rect[2] == 0 and rect[4] == 181 then
                -- the menu list: its first four lines only (the fifth, y 136-172, is the website)
                local copy = {}
                for key, value in pairs(command) do copy[key] = value end
                copy[3] = {0, 0, rect[3], 136}
                kept[#kept + 1] = copy
            elseif sheet and command[5] >= OPTIONS[1] - 8 and command[5] <= OPTIONS[2] then
                -- the letters of "options": up into the website row
                local copy = {}
                for key, value in pairs(command) do copy[key] = value end
                copy[5] = command[5] - SHIFT
                kept[#kept + 1] = copy
            else
                kept[#kept + 1] = command
            end
        end
        state.display = kept
        return result
    end

    return base
end

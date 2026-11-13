return function(base)
  function base.create(o)
    local catalog = require("base/game/catalog")
    local match = require("base/game/match")
    local fighters, bgs = catalog.load(), catalog.backgrounds()
    local out = {}
    local function log(s) out[#out+1] = s end
    local dn, dp
    for i, f in ipairs(fighters) do
      if f.record == nil then log("NIL RECORD " .. f.name) end
      if f.id == 61 then dn = i end; if f.id == 1 then dp = i end
    end
    local s = match.create({mode = require("base/game/constants").modes.versus, difficulty = 0, background = 0,
      fighters = fighters, backgrounds = bgs, slots = {[0] = {kind = "human", fighter = dn, team = 1}, [1] = {kind = "human", fighter = dp, team = 2}}})
    s = s.state or s
    local A, B = s.items[0], s.items[1]
    -- hitbox alignment: body box of frame 0 relative to the feet, DarthNox vs Deep
    local fa, fb = A.record.frame(0), B.record.frame(0)
    local ba, bb = fa.bodies[1], fb.bodies[1]
    log(string.format("body box rel. feet: DarthNox x %d..%d y %d..%d | Deep x %d..%d y %d..%d",
      ba.x - fa.center_x, ba.x + ba.width - fa.center_x, ba.y - fa.center_y, ba.y + ba.height - fa.center_y,
      bb.x - fb.center_x, bb.x + bb.width - fb.center_x, bb.y - fb.center_y, bb.y + bb.height - fb.center_y))
    local pa, pb = A.record.frame(61).interactions[1], B.record.frame(61).interactions[1]
    log(string.format("punch box rel. feet: DarthNox x %d..%d | Deep x %d..%d", pa.x - A.record.frame(61).center_x, pa.x + pa.width - A.record.frame(61).center_x,
      pb.x - B.record.frame(61).center_x, pb.x + pb.width - B.record.frame(61).center_x))
    local function step(p0, p1)
      local held = {functions = "", keys = {}, function_presses = ""}
      for k = 0, 7 do held[k] = "" end
      held[0], held[1] = p0 or "", p1 or ""
      match.step(s, held)
    end
    for i = 1, 220 do step() end
    local function place(ax, bx, mp)
      for k = 1, 40 do step() end
      for _, v in ipairs({A, B}) do v.vx, v.vy, v.vz, v.frame = 0, 0, 0, 0 end
      A.x, A.x_int, B.x, B.x_int = ax, ax, bx, bx
      A.z, A.z_int, B.z, B.z_int = 400, 400, 400, 400
      A.facing, B.facing = 0, 1
      A.mp, B.mp, A.hp, B.hp = mp or 500, 500, 500, 500
      step()
    end
    local function run(name, seq, n)
      local seen, seenB = {}, {}
      local hpA, hpB, mp0, x0 = A.hp, B.hp, A.mp, A.x
      local peak, hits, lastB, airborne_phases, wasAir = 0, 0, B.hp, 0, false
      local ballX0, ballX1, ballTicks = nil, nil, 0
      local function tick(p0, p1)
        step(p0, p1)
        if seen[#seen] ~= A.frame then seen[#seen+1] = A.frame end
        if seenB[#seenB] ~= B.frame then seenB[#seenB+1] = B.frame end
        if -A.y > peak then peak = -A.y end
        local air = A.y < -0.5
        if air and not wasAir then airborne_phases = airborne_phases + 1 end
        wasAir = air
        if B.hp < lastB then hits = hits + 1; lastB = B.hp end
        local seenBall = false
        for k = 20, 150 do local v = s.items[k]; if v and v.record.id == 62 then seenBall = true; ballX0 = ballX0 or v.x; ballX1 = v.x end end
        if seenBall then ballTicks = ballTicks + 1 end
      end
      for _, tok in ipairs(seq) do
        local p0, p1 = tok:match("^([^/]*)/?(.*)$")
        tick(p0, p1); tick(p0, p1); tick()
      end
      for k = 1, n do tick() end
      log(string.format("%s: A %s\n    B %s\n    dmg to Deep %d in %d hits, to DarthNox %d | MP %d->%d | peak %.0f px, airborne phases %d | moved %.0f px%s",
        name, table.concat(seen, ","), table.concat(seenB, ","), hpB - B.hp, hits, hpA - A.hp, mp0, A.mp, peak, airborne_phases, A.x - x0,
        ballX0 and string.format(" | crescent %.0f px in %d ticks (%.1f px/tick)", ballX1 - ballX0, ballTicks, (ballX1 - ballX0) / math.max(1, ballTicks)) or ""))
    end
    place(200, 760); run("D>A crescent (no target)", {"f", "r", "c"}, 80)
    place(200, 760); run("D>J lunge (no target)", {"f", "r", "b"}, 40)
    place(200, 290); run("D>J lunge vs Deep", {"f", "r", "b"}, 40)
    place(200, 760); run("D^A miss", {"f", "u", "c"}, 50)
    place(200, 240); run("D^A hit", {"f", "u", "c"}, 50)
    place(200, 250); run("DvA flurry, mash A", {"f", "d", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c"}, 30)
    place(200, 250, 70); run("DvA flurry, mash A, low MP", {"f", "d", "c", "c", "c", "c", "c", "c", "c", "c"}, 30)
    place(300, 345); run("DarthNox punch", {"c"}, 30)
    place(300, 345); run("Deep punch", {"/c"}, 30)
    place(300, 345); run("DJA parry vs punch", {"f", "b", "c", "/c"}, 70)
    error("\n" .. table.concat(out, "\n"))
  end
  return base
end

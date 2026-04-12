/**
 * Octopus Banner — pixel-art octopus with cycling quotes
 *
 * Draws two octopus variants (Sassy + Supportive) on canvas elements
 * and cycles through their quote pools with a typewriter effect.
 */
(function () {
  "use strict";

  // ── Octopus body pixel data (run-length encoded) ──
  // Format: [y, [[x0,x1], ...]] — same data as the DevTool Python source
  var BODY = [
    [10,[[22,48]]],[11,[[18,52]]],[12,[[16,54]]],[13,[[14,56]]],
    [14,[[13,57]]],[15,[[12,58]]],[16,[[11,59]]],[17,[[10,60]]],
    [18,[[10,60]]],[19,[[9,61]]],[20,[[9,61]]],[21,[[9,61]]],
    [22,[[9,61]]],[23,[[9,61]]],[24,[[9,61]]],[25,[[9,61]]],
    [26,[[9,61]]],[27,[[9,61]]],[28,[[10,60]]],[29,[[10,60]]],
    [30,[[10,60]]],[31,[[10,60]]],[32,[[10,60]]],[33,[[10,60]]],
    [34,[[10,60]]],[35,[[10,60]]],[36,[[10,60]]],[37,[[10,60]]],
    [38,[[10,60]]],[39,[[10,60]]],[40,[[10,60]]],[41,[[11,59]]],
    [42,[[11,59]]],[43,[[12,58]]],[44,[[13,57]]],[45,[[14,56]]],
    [46,[[12,58]]],[47,[[11,59]]],[48,[[10,60]]],[49,[[10,60]]],
    [50,[[11,59]]],[51,[[12,58]]],[52,[[13,57]]],[53,[[14,56]]],
    [54,[[15,55]]],
    // Tentacles
    [55,[[10,17],[21,28],[32,39],[43,50],[54,61]]],
    [56,[[8,15],[19,26],[30,37],[45,52],[56,63]]],
    [57,[[7,14],[18,24],[29,35],[47,53],[58,64]]],
    [58,[[6,12],[19,25],[31,37],[46,52],[57,63]]],
    [59,[[7,13],[21,27],[33,39],[44,50],[55,61]]],
    [60,[[8,14],[20,26],[31,37],[43,49],[54,60]]],
    [61,[[9,14],[18,24],[30,36],[44,50],[56,62]]],
    [62,[[8,13],[17,22],[31,37],[46,52],[57,63]]],
    [63,[[7,12],[18,23],[33,38],[45,51],[55,61]]],
    [64,[[8,13],[20,25],[32,37],[43,48],[54,59]]],
    [65,[[9,14],[19,24],[30,35],[44,49],[55,60]]],
    [66,[[10,14],[17,22],[31,36],[46,51],[57,62]]],
    [67,[[9,13],[18,22],[33,37],[45,50],[56,61]]],
    [68,[[8,12],[19,23],[32,36],[43,48],[54,59]]],
    [69,[[9,13],[21,25],[30,34],[44,48],[55,59]]],
    [70,[[10,14],[20,24],[31,35],[46,50],[57,61]]],
    [71,[[11,14],[18,22],[33,37],[45,49],[56,60]]],
    [72,[[10,13],[19,22],[32,35],[43,47],[54,58]]],
    [73,[[9,12],[20,23],[30,33],[44,47],[55,58]]],
    [74,[[10,13],[21,24],[31,34],[46,49],[57,60]]],
    [75,[[11,14],[20,23],[33,36],[45,48],[56,59]]],
    [76,[[12,14],[19,22],[32,35],[43,46],[54,57]]],
    [77,[[11,13],[20,22],[30,33],[44,46],[55,57]]],
    [78,[[10,12],[21,23],[31,33],[45,47],[56,58]]],
    [79,[[11,13],[22,24],[32,34],[44,46],[55,57]]],
    [80,[[12,14],[21,23],[33,35],[43,45],[54,56]]]
  ];

  // Eye sockets (white circles), pupils (black dots), highlights (white sparkle)
  function circlePixels(cx, cy, rSq) {
    var r = Math.ceil(Math.sqrt(rSq));
    var pts = [];
    for (var dy = -r; dy <= r; dy++)
      for (var dx = -r; dx <= r; dx++)
        if (dx * dx + dy * dy <= rSq)
          pts.push([cx + dx, cy + dy]);
    return pts;
  }

  var EYES = circlePixels(22, 25, 16).concat(circlePixels(48, 25, 16));
  var PUPILS = circlePixels(23, 26, 4).concat(circlePixels(49, 26, 4));
  var HIGHLIGHTS = circlePixels(20, 23, 1).concat(circlePixels(46, 23, 1));

  // Smirk mouth
  function smirkPixels() {
    var outline = [], interior = [];
    for (var x = 28; x < 44; x++) {
      var t = (x - 28) / 15.0;
      var tilt = -2 + t * 4;
      var v = 2 * t - 1;
      var arc = Math.abs(v) < 1 ? 5 * Math.sqrt(1 - v * v) : 0;
      var yc = 39 + tilt + arc;
      outline.push([x, Math.floor(yc - 1)]);
      outline.push([x, Math.floor(yc + 1)]);
      interior.push([x, Math.floor(yc)]);
    }
    return { outline: outline, interior: interior };
  }

  // ── Draw octopus on a canvas ──
  function drawOctopus(canvas, scale) {
    var s = scale || 2;
    canvas.width = 70 * s;
    canvas.height = 85 * s;
    var ctx = canvas.getContext("2d");

    // Pixel buffer (70x85 region — the octopus lives in roughly x:5-65, y:8-82)
    var W = 70, H = 85, offX = 0, offY = -5;
    var buf = [];
    for (var i = 0; i < H; i++) buf[i] = new Uint8Array(W);

    // Body
    BODY.forEach(function (row) {
      var y = row[0] + offY;
      if (y < 0 || y >= H) return;
      row[1].forEach(function (span) {
        for (var x = Math.max(0, span[0] + offX); x <= Math.min(W - 1, span[1] + offX); x++)
          buf[y][x] = 1;
      });
    });

    // Eyes (white)
    EYES.forEach(function (p) {
      var x = p[0] + offX, y = p[1] + offY;
      if (x >= 0 && x < W && y >= 0 && y < H) buf[y][x] = 0;
    });

    // Pupils (black)
    PUPILS.forEach(function (p) {
      var x = p[0] + offX, y = p[1] + offY;
      if (x >= 0 && x < W && y >= 0 && y < H) buf[y][x] = 1;
    });

    // Highlights (white)
    HIGHLIGHTS.forEach(function (p) {
      var x = p[0] + offX, y = p[1] + offY;
      if (x >= 0 && x < W && y >= 0 && y < H) buf[y][x] = 0;
    });

    // Smirk
    var smirk = smirkPixels();
    smirk.interior.forEach(function (p) {
      var x = p[0] + offX, y = p[1] + offY;
      if (x >= 0 && x < W && y >= 0 && y < H) buf[y][x] = 0;
    });
    smirk.outline.forEach(function (p) {
      var x = p[0] + offX, y = p[1] + offY;
      if (x >= 0 && x < W && y >= 0 && y < H) buf[y][x] = 1;
    });

    // Render to canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var y = 0; y < H; y++)
      for (var x = 0; x < W; x++)
        if (buf[y][x]) {
          ctx.fillStyle = "#cdd6f4";
          ctx.fillRect(x * s, y * s, s, s);
        }
  }

  // ── Quotes ──
  var SASSY = [
    "WIFI IS JUST SPICY AIR.",
    "FISH ARE JUST WET BIRDS.",
    "I DONT HAVE BONES AND THATS A FLEX.",
    "MATTRESSES ARE BODY SHELVES.",
    "THE OCEAN IS JUST SKY JUICE.",
    "SLEEP IS FREE DEATH TRIAL.",
    "STAIRS ARE JUST BROKEN ESCALATORS.",
    "THE FLOOR IS JUST A BIG SHELF.",
    "DOORS ARE WALLS THAT GAVE UP.",
    "EGGS ARE JUST BONELESS CHICKENS.",
    "IM 90% WATER. IM BASICALLY A SPLASH.",
    "SAND IS JUST ANGRY ROCKS.",
    "TREES ARE JUST GROUND HAIR.",
    "LAVA IS JUST EARTH SAUCE.",
    "MATH IS JUST SPICY COUNTING.",
    "SOCKS ARE JUST FOOT PRISONS.",
    "A BURRITO IS A SLEEPING BAG FOR FOOD.",
    "INK IS MY DEFENSE MECHANISM. AND COMEDY.",
    "8 ARMS AND ZERO PATIENCE.",
    "SPAGHETTI IS JUST BONELESS TENTACLES.",
    "JELLYFISH ARE JUST OCEAN GHOSTS.",
    "I HUG THINGS 4X BETTER THAN YOU.",
    "IM TOO PRETTY FOR THIS DAMN OCEAN.",
    "DONT TALK TO ME BEFORE MY KELP COFFEE.",
    "I DIDNT ASK TO BE THIS FABULOUS.",
    "CATCH ME OUTSIDE THE REEF. HOW BOUT DAT.",
    "YOUR OPINION MEANS LESS THAN PLANKTON TO ME.",
    "SORRY CANT HEAR YOU OVER MY 8 ARM ENERGY.",
    "WHAT THE SHELL DID YOU JUST SAY TO ME.",
    "YOURE ABOUT AS USEFUL AS A SCREEN DOOR ON A SUBMARINE.",
    "I HAVE 3 HEARTS AND NONE OF THEM CARE.",
    "BOLD WORDS FROM SOMEONE WITH ONLY 2 ARMS.",
    "OH HELL NO. ABSOLUTELY NOT. NEXT.",
    "THE AUDACITY. THE DAMN AUDACITY.",
    "BIRDS ARENT REAL. THEY CHARGE ON POWER LINES!",
    "PIGEONS ARE DRONES. WAKE UP SHEEPLE.",
    "CLOUDS ARE GOVERNMENT PILLOWS.",
    "THE MOON IS JUST THE BACK OF THE SUN.",
    "GRAVITY IS A SUBSCRIPTION SERVICE.",
    "MIRRORS ARE JUST WATER THAT TRIED HARDER.",
    "YOUR SKELETON IS WET RIGHT NOW. THINK ABOUT IT.",
    "OCTOBER HAS NO OCTOS IN IT. SUS AS HELL.",
    "TREES ARE SURVEILLANCE ANTENNAS. LOOK IT UP.",
    "RAIN IS JUST THE SKY PEEING. PROVE ME WRONG.",
    "THE ALPHABET IS IN THAT ORDER FOR A DAMN REASON.",
    "BELLY BUTTONS ARE JUST OLD MOUTHS.",
    "YAWNING IS YOUR SKULL TRYING TO ESCAPE.",
    "SHADOWS ARE JUST 2D VERSIONS OF YOU SPYING.",
    "DEJA VU IS THE SIMULATION BUFFERING.",
    "HICCUPS ARE YOUR BODY GLITCHING.",
    "THE DEEP STATE RUNS APPLEBEES.",
    "MATTRESS FIRM IS A MONEY LAUNDERING FRONT.",
    "FINLAND DOESNT EXIST. GOOGLE IT.",
    "WYOMING IS JUST A GOVERNMENT PRANK.",
    "AUSTRALIA IS UPSIDE DOWN AND FAKE.",
    "THE BERMUDA TRIANGLE IS MY VACATION HOME.",
    "5G TURNED MY NEIGHBOR INTO A ROUTER.",
    "THE TITANIC WAS AN INSURANCE SCAM.",
    "DENVER AIRPORT IS AN ILLUMINATI CLUBHOUSE.",
    "BIGFOOT IS REAL AND HES A DAMN GENTLEMAN.",
    "FLAT EARTHERS ARE SECRETLY ROUND.",
    "CROP CIRCLES ARE JUST ALIEN DOODLES.",
    "WHAT IF YOUR LEGS DIDNT KNOW THEY WERE LEGS.",
    "I JUST REALIZED WATER IS BONELESS ICE.",
    "EVERY ROOM IS AN ESCAPE ROOM IF YOU SUCK.",
    "CORN IS JUST FRUIT WITH EXTRA STEPS.",
    "SOUP IS JUST WET SALAD. FIGHT ME.",
    "ELEVATORS ARE JUST ROOMS THAT MOVE. WHAT THE HELL.",
    "COFFINS ARE UNDERGROUND TINY HOMES.",
    "A FLY WITHOUT WINGS IS JUST A WALK.",
    "GLOVES ARE JUST HAND SOCKS. HAND. SOCKS.",
    "A KEYBOARD IS JUST AN ORGANIZED ALPHABET.",
    "THE SUN IS A DEADLY LAZER BUT WE JUST VIBE.",
    "THE MARIANA TRENCH IS WHERE GOD DROPPED HIS KEYS.",
    "THERE ARE THINGS IN THE DEEP OCEAN THAT WOULD MAKE GOD CRY.",
    "THE OCEAN IS JUST A BIG ASS SOUP AND WERE ALL CROUTONS.",
    "ANGLERFISH INVENTED CATFISHING AND NOBODY GIVES THEM CREDIT.",
    "WHALES ARE JUST FAT SUBMARINES CHANGE MY DAMN MIND.",
    "THE KRAKEN IS REAL AND ITS MY COUSIN STEVE.",
    "CORAL REEFS ARE JUST UNDERWATER CITIES WE KEEP MURDERING.",
    "DOLPHINS ARE PSYCHOPATHS WITH GOOD PR.",
    "SHRIMP ON A TREADMILL WAS FUNDED BY YOUR TAXES.",
    "THE OCEAN FLOOR IS LESS MAPPED THAN MARS AND THAT PISSES ME OFF.",
    "NOTHING MATTERS AND THATS ACTUALLY PRETTY DAMN FREEING.",
    "WE ARE ALL JUST MEAT COMPUTERS HAVING A BAD TIME.",
    "TIME IS FAKE. CLOCKS ARE A CONSPIRACY.",
    "WHAT IF WE ARE ALL JUST NPCS IN SOMEONES GAME.",
    "THE VOID STARED BACK AND IT WINKED AT ME.",
    "REALITY IS A SHARED HALLUCINATION AND THE RENT IS TOO DAMN HIGH.",
    "IF ATOMS ARE MOSTLY EMPTY SPACE THEN IM MOSTLY NOTHING. COOL.",
    "EVERY SECOND YOU EXIST IS STATISTICALLY INSANE.",
    "THE FACT THAT ANYTHING EXISTS AT ALL IS BATSHIT.",
    "FREE WILL IS JUST ANXIETY WITH A MARKETING TEAM.",
    "I HAVE SEEN THE FACE OF GOD AND IT WAS AN OCTOPUS.",
    "THEY PUT CHEMICALS IN THE WATER TO MAKE THE DAMN FROGS GAY.",
    "EVERYTHING IS CAKE. LITERALLY EVERYTHING. CUT INTO YOUR DESK.",
    "THE SIMULATION IS RUNNING OUT OF RAM AND ITS SHOWING.",
    "TUPAC IS ALIVE AND WORKING AT A TARGET IN OHIO.",
    "BIRDS WORK FOR THE BOURGEOISIE.",
    "EARTH IS A REALITY TV SHOW FOR ALIENS AND WE ARE LOSING.",
    "MOTHMAN IS JUST A BIG MOTH WHO BELIEVES IN HIMSELF.",
    "SKINWALKER RANCH IS JUST A PETTING ZOO FOR CRYPTIDS.",
    "FLUORIDE IN WATER MAKES YOU FORGET THAT BIRDS ARENT REAL.",
    "I HAVE 3 HEARTS AND ALL OF THEM ARE PETTY.",
    "MY BLOOD IS LITERALLY BLUE. IM ROYALTY. BOW.",
    "I CAN CHANGE COLOR. CAN YOU DO THAT. NO. SIT DOWN.",
    "I CAN FIT THROUGH ANY HOLE BIGGER THAN MY BEAK. TRY ME.",
    "I ONCE UNSCREWED A JAR FROM THE INSIDE. WHAT HAVE YOU DONE.",
    "MY BRAIN IS SHAPED LIKE A DONUT AND ITS STILL SMARTER THAN YOU.",
    "I HAVE SEEN THINGS IN THE ABYSS THAT WOULD MELT YOUR PATHETIC LITTLE MIND.",
    "I ESCAPED AN AQUARIUM ONCE. ILL DO IT AGAIN.",
    "EACH OF MY ARMS HAS ITS OWN BRAIN. THATS 9 BRAINS TOTAL YOU ABSOLUTE WALNUT.",
    "I COULD DISASSEMBLE YOUR ENTIRE LIFE WITH 8 ARMS AND ZERO REMORSE.",
    "LASAGNA IS JUST SPAGHETTI CAKE.",
    "A HOTDOG IS A TACO. I WILL DIE ON THIS HILL.",
    "CEREAL IS BREAKFAST SOUP AND YOU KNOW IT.",
    "PANCAKES ARE JUST FLAT BREAD WITH AN EGO.",
    "RAISINS ARE JUST GRAPES THAT GAVE UP ON LIFE.",
    "ICE IS JUST WATER WITH COMMITMENT ISSUES.",
    "PICKLES ARE JUST CUCUMBERS THAT WENT THROUGH SOME SHIT.",
    "POPCORN IS JUST CORN HAVING A PANIC ATTACK.",
    "TOAST IS JUST TWICE BAKED BREAD. WHY.",
    "CROUTONS ARE JUST BREAD THAT DIED AND CAME BACK HARDER."
  ];

  var SUPPORTIVE = [
    "YOU ARE DOING SO DAMN GOOD RIGHT NOW.",
    "HEY. HEY YOU. YOURE INCREDIBLE. DEAL WITH IT.",
    "I HAVE 8 ARMS AND ID USE THEM ALL TO HUG YOU.",
    "YOURE THE REASON I BELIEVE IN LAND PEOPLE.",
    "GO DRINK SOME WATER YOU BEAUTIFUL DISASTER.",
    "YOU ABSOLUTE LEGEND. I MEAN IT. LEGEND.",
    "YOUR EXISTENCE IS MY FAVORITE THING TODAY.",
    "IM SO PROUD OF YOU IT MAKES MY TENTACLES TINGLE.",
    "YOU WOKE UP TODAY AND CHOSE BEING AWESOME.",
    "YOURE DOING GREAT SWEETIE AND I WILL FIGHT ANYONE WHO SAYS OTHERWISE.",
    "IF LIFE GIVES YOU LEMONS I WILL STRANGLE LIFE FOR YOU.",
    "YOU COULD BENCH PRESS MY EMOTIONS RIGHT NOW.",
    "YOURE NOT A MESS YOURE A MASTERPIECE WITH EXTRA TEXTURE.",
    "I WOULD COMMIT CRIMES FOR YOUR HAPPINESS. SMALL ONES.",
    "THE UNIVERSE MADE YOU ON PURPOSE AND I RESPECT THE HELL OUT OF THAT.",
    "LISTEN. YOURE A SNACK. AN ENTIRE BUFFET ACTUALLY.",
    "YOUR VIBE IS IMMACULATE AND ANYONE WHO DISAGREES CAN CATCH THESE ARMS.",
    "I BELIEVE IN YOU MORE THAN I BELIEVE IN DRY LAND.",
    "YOURE THE MAIN CHARACTER AND EVERYONE ELSE IS AN NPC.",
    "IF YOURE READING THIS CONGRATS YOURE AMAZING AS HELL.",
    "STOP DOUBTING YOURSELF BEFORE I INK ON YOUR PROBLEMS.",
    "YOU DIDNT COME THIS FAR TO ONLY COME THIS FAR.",
    "HATERS GONNA HATE BUT YOU GONNA SLAY.",
    "YOURE NOT TIRED YOURE ON THE VERGE OF GREATNESS.",
    "FAILURE IS JUST SUCCESS IN A REALLY UGLY OUTFIT.",
    "GET UP BESTIE WE HAVE BUTTS TO KICK TODAY.",
    "YOUR POTENTIAL IS SCARIER THAN THE DEEP OCEAN.",
    "IM 90% WATER AND 100% ROOTING FOR YOU.",
    "EVERY DAY YOU WAKE UP IS ANOTHER DAY TO BE A BADASS.",
    "YOU ARE LITERALLY TOO POWERFUL TO GIVE UP NOW.",
    "THE AUDACITY OF YOU BEING THIS WONDERFUL. HOW DARE YOU.",
    "YOURE NOT AWKWARD YOURE LIMITED EDITION.",
    "MY THIRD ARM JUST GAVE YOU A THUMBS UP.",
    "YOURE LIKE WIFI BUT FOR GOOD VIBES.",
    "IF YOU WERE A FISH ID THROW YOU BACK. BECAUSE YOURE FREE. GO LIVE.",
    "YOUR HEART IS BIGGER THAN MY ENTIRE HEAD. AND IM MOSTLY HEAD.",
    "I DONT HAVE A SPINE AND EVEN I THINK YOURE BRAVE.",
    "YOU RADIATE THE SAME ENERGY AS A REALLY GOOD SUNSET.",
    "SOMEONE OUT THERE IS SMILING BECAUSE OF YOU. ITS ME. IM SOMEONE.",
    "YOURE THE PLOT TWIST EVERYONE NEEDED.",
    "DID YOU EAT TODAY YOU MAGNIFICENT CREATURE.",
    "DRINK WATER OR I SWEAR ON MY TENTACLES.",
    "TAKE A DEEP BREATH. DEEPER. I SAID DEEPER. GOOD.",
    "REST IS NOT LAZY ITS TACTICAL. NOW SIT DOWN.",
    "YOU CANT POUR FROM AN EMPTY CUP SO REFILL YOURSELF DAMMIT.",
    "SLEEP IS NOT FOR THE WEAK ITS FOR THE POWERFUL. GO NAP.",
    "YOUR FEELINGS ARE VALID EVEN THE WEIRD ONES.",
    "BE NICE TO YOURSELF OR ILL SQUIRT INK AT YOU.",
    "ITS OK TO NOT BE OK BUT PLEASE EAT A VEGETABLE.",
    "YOU DESERVE GOOD THINGS AND ALSO A REALLY GOOD SANDWICH.",
    "I WOULD SHARE MY FAVORITE ROCK WITH YOU. THATS HUGE.",
    "YOURE MY FAVORITE HUMAN AND I LIVE IN THE OCEAN.",
    "IF I COULD HIGH FIVE ID DO IT 8 TIMES.",
    "YOU MAKE ME WANT TO COME OUT OF MY HIDING SPOT.",
    "I WROTE YOUR NAME IN INK. ON THE OCEAN FLOOR. FOREVER.",
    "MY HEARTS AND YES I HAVE THREE ALL BEAT FOR YOU.",
    "YOU ARE THE TREASURE THAT PIRATES WERE LOOKING FOR.",
    "I WOULD FIGHT A SHARK FOR YOU. NOT A BIG ONE BUT STILL.",
    "IN A SEA OF FISH YOU ARE THE WHOLE DAMN OCEAN.",
    "YOURE PROOF THAT GOOD THINGS EXIST ON LAND.",
    "TODAYS MOOD IS UNSTOPPABLE AND SLIGHTLY UNHINGED.",
    "YOURE ABOUT TO DO SOMETHING AMAZING I CAN FEEL IT IN MY SUCKERS.",
    "PLOT TWIST YOURE THE HERO OF THIS STORY.",
    "SCARED IS JUST EXCITED WITH BAD BRANDING.",
    "YOU MISS 100% OF THE SHOTS YOU DONT TAKE. I MISS 0% BECAUSE 8 ARMS.",
    "NORMALIZE BEING PROUD OF YOURSELF FOR NO REASON.",
    "THE ONLY OPINION THAT MATTERS IS YOURS. AND MINE. AND MINE SAYS YOURE GREAT.",
    "IF PLAN A DIDNT WORK THERE ARE 25 MORE LETTERS. KEEP GOING.",
    "YOURE NOT BEHIND IN LIFE. YOURE ON YOUR OWN DAMN TIMELINE.",
    "THE COMEBACK IS ALWAYS STRONGER THAN THE SETBACK.",
    "I LOVE YOU LIKE THE OCEAN LOVES BEING WET.",
    "YOU ARE THE REASON I HAVE TRUST IN BIPEDS.",
    "IF HUGS WERE CURRENCY ID BE A BILLIONAIRE FOR YOU.",
    "YOURE GLOWING AND NOT IN A RADIOACTIVE WAY. PROBABLY.",
    "I STAN YOU SO HARD ALL 8 ARMS ARE CLAPPING.",
    "YOURE A WHOLE VIBE AND THAT VIBE IS PHENOMENAL.",
    "GO BE GREAT TODAY OR DONT. ILL LOVE YOU EITHER WAY.",
    "MY FAVORITE THING ABOUT YOU IS EVERYTHING.",
    "YOURE NOT JUST A STAR YOURE THE WHOLE CONSTELLATION.",
    "KEEP GOING BESTIE THE OCEAN BELIEVES IN YOU."
  ];

  // Shuffle helper
  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
    }
    return arr;
  }

  // ── Build combined quote pool ──
  function buildPool() {
    var pool = [];
    shuffle(SASSY.slice()).forEach(function (q) {
      pool.push({ text: q, mode: "sassy" });
    });
    shuffle(SUPPORTIVE.slice()).forEach(function (q) {
      pool.push({ text: q, mode: "supportive" });
    });
    return shuffle(pool);
  }

  // ── Initialize banner ──
  function init() {
    var container = document.getElementById("octopus-banner");
    if (!container) return;

    // Build DOM
    container.innerHTML =
      '<div class="octo-banner-inner">' +
        '<canvas class="octo-banner-canvas" aria-hidden="true"></canvas>' +
        '<div class="octo-banner-text">' +
          '<span class="octo-banner-mode">~ SASSY OCTOPUS ~</span>' +
          '<span class="octo-banner-quote"></span>' +
        '</div>' +
        '<canvas class="octo-banner-canvas octo-banner-canvas-right" aria-hidden="true"></canvas>' +
      '</div>';

    var canvases = container.querySelectorAll(".octo-banner-canvas");
    var modeEl = container.querySelector(".octo-banner-mode");
    var quoteEl = container.querySelector(".octo-banner-quote");

    // Pick scale based on viewport
    var scale = window.innerWidth < 600 ? 1 : 2;
    drawOctopus(canvases[0], scale);
    drawOctopus(canvases[1], scale);
    // Flip the right one
    canvases[1].style.transform = "scaleX(-1)";

    // Quote cycling
    var pool = buildPool();
    var idx = 0;
    var charIdx = 0;
    var current = pool[0];
    var typing = true;
    var pauseFrames = 0;

    function updateMode(mode) {
      if (mode === "supportive") {
        modeEl.textContent = "~ SUPPORTIVE OCTOPUS ~";
        modeEl.className = "octo-banner-mode octo-mode-supportive";
      } else {
        modeEl.textContent = "~ SASSY OCTOPUS ~";
        modeEl.className = "octo-banner-mode octo-mode-sassy";
      }
    }

    function tick() {
      if (pauseFrames > 0) {
        pauseFrames--;
        return;
      }

      if (typing) {
        charIdx++;
        quoteEl.textContent = current.text.substring(0, charIdx);
        if (charIdx >= current.text.length) {
          typing = false;
          pauseFrames = 60; // ~3s pause at full quote
        }
      } else {
        // Move to next quote
        idx = (idx + 1) % pool.length;
        if (idx === 0) pool = buildPool(); // reshuffle when exhausted
        current = pool[idx];
        charIdx = 0;
        typing = true;
        updateMode(current.mode);
        quoteEl.textContent = "";
      }
    }

    updateMode(current.mode);
    setInterval(tick, 50);
  }

  // Run on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

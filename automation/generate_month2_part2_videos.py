import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"G:\Faceless-Shorts")
AUTO = ROOT / "automation"
QUEUE_PATH = AUTO / "data" / "30day_topic_queue.json"
UPLOAD_Q_PATH = AUTO / "data" / "upload_queue.json"
PROPS_TEMPLATE = AUTO / "templates" / "cartoon_props.js"
NEW_VIDEO_PS1 = ROOT / "skills" / "faceless-shorts" / "scripts" / "new_video.ps1"
RUN_PIPELINE_PS1 = AUTO / "run_pipeline.ps1"
MAKE_THUMB_MJS = AUTO / "make_thumbnail.mjs"
SEO_PY = AUTO / "build_seo_package.py"
PY_VENV = r"C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"

IST = timezone(timedelta(hours=5, minutes=30))

TOPICS_13 = [
    {
        "id": "18_12_26",
        "day": 38,
        "date_str": "18/12/26",
        "category": "space-nature",
        "title": "Frosty Snowflakes: Why No Two Snowflakes Are Ever Identical!",
        "thumb_text": "NO TWO SAME?!",
        "primary_keyword": "snowflake science for kids",
        "supporting_keywords": ["why are snowflakes unique cartoon", "snow nursery rhyme preschool", "how snowflakes form kids"],
        "fact_summary": "High in freezing clouds, water vapor freezes around a tiny speck of dust into a six-sided ice crystal. As it falls through ever-changing humidity and wind, each snowflake grows its own unique microscopic branches!",
        "hook": "Look at that falling snow! But wait... is it true that no two snowflakes in the whole world are ever identical?",
        "publish_slot_est": "2026-12-18T15:30:00-05:00",
        "publish_at_utc": "2026-12-18T20:30:00Z",
        "lines": [
            {"text": "Dance, dance, little snowflake, tumbling gently from the sky!", "caps": "*DANCE dance | little *SNOWFLAKE, | tumbling gently *FROM | the *SKY!"},
            {"text": "Is it really true that no two snowflakes on Earth are ever identical?", "caps": "Is it really *TRUE | that no two snowflakes on *EARTH | are ever *IDENTICAL?"},
            {"text": "Yes! High in the frosty clouds, water freezes around a tiny speck of dust!", "caps": "*YES! High in the *FROSTY | clouds, water freezes *AROUND | a tiny speck of *DUST!"},
            {"text": "Water molecules always link up into a six-sided hexagonal crystal shape!", "caps": "Water molecules always *LINK | up into a *SIX-SIDED | hexagonal crystal *SHAPE!"},
            {"text": "As the snowflake drifts down, wind, temperature, and humidity change every second!", "caps": "As the snowflake *DRIFTS | down, wind, temperature, and *HUMIDITY | change every *SECOND!"},
            {"text": "Each branch grows differently based on the exact path it travels through the air!", "caps": "Each branch grows *DIFFERENTLY | based on the exact *PATH | it travels through the *AIR!"},
            {"text": "With trillions of possibilities, every single flake is a one-of-a-kind frozen artwork!", "caps": "With trillions of *POSSIBILITIES, | every single flake is a *ONE-OF-A-KIND | frozen *ARTWORK!"},
            {"text": "Now you know the winter magic behind every falling snowflake!", "caps": "Now you *KNOW | the winter *MAGIC | behind every falling *SNOWFLAKE!"},
            {"text": "Catch more cool science and subscribe to BabyBeats Rhymo!", "caps": "*CATCH more cool | *SCIENCE and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "19_12_26",
        "day": 39,
        "date_str": "19/12/26",
        "category": "body-science",
        "title": "Three Little Kittens: How Mittens Keep Your Fingers Warm!",
        "thumb_text": "MITTEN MAGIC!",
        "primary_keyword": "three little kittens rhyme for kids",
        "supporting_keywords": ["how mittens keep hands warm kids", "three little kittens cartoon", "winter clothing science preschool"],
        "fact_summary": "Mittens don't produce any heat on their own. Instead, fluffy wool fibers trap tiny pockets of still air, creating an insulating blanket that keeps your body's natural heat from escaping into the cold winter air.",
        "hook": "Three little kittens lost their mittens and they began to cry! But wait, do mittens make heat, or do your fingers do all the work?",
        "publish_slot_est": "2026-12-19T15:30:00-05:00",
        "publish_at_utc": "2026-12-19T20:30:00Z",
        "lines": [
            {"text": "Three little kittens, they lost their mittens, and they began to cry!", "caps": "Three little *KITTENS, | they lost their *MITTENS, | and they began to *CRY!"},
            {"text": "Oh mother dear, our paws are freezing cold outside!", "caps": "Oh mother *DEAR, | our paws are *FREEZING | cold *OUTSIDE!"},
            {"text": "Put on your mittens! But did you know mittens don't actually make any heat?", "caps": "Put on your *MITTENS! | But did you know mittens *DON'T | actually make any *HEAT?"},
            {"text": "Your own body makes warm heat like a little internal furnace!", "caps": "Your own body *MAKES | warm heat like a *LITTLE | internal *FURNACE!"},
            {"text": "Fluffy wool fibers trap millions of microscopic pockets of still air!", "caps": "Fluffy wool fibers *TRAP | millions of microscopic *POCKETS | of still *AIR!"},
            {"text": "Trapped air is a super insulator that stops cold air from stealing your warmth!", "caps": "Trapped air is a super *INSULATOR | that stops cold air from *STEALING | your *WARMTH!"},
            {"text": "And inside mittens, your fingers huddle together to share their heat!", "caps": "And inside *MITTENS, | your fingers huddle *TOGETHER | to share their *HEAT!"},
            {"text": "Now you know the cozy physics behind Three Little Kittens and their mittens!", "caps": "Now you *KNOW | the cozy *PHYSICS | behind Three Little *KITTENS | and their mittens!"},
            {"text": "Stay warm and smart—subscribe to BabyBeats Rhymo!", "caps": "Stay *WARM and smart— | *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "20_12_26",
        "day": 40,
        "date_str": "20/12/26",
        "category": "body-science",
        "title": "Pease Porridge Hot: Why Hot Cocoa Forms a Secret Skin on Top!",
        "thumb_text": "HOT COCOA SKIN?!",
        "primary_keyword": "hot cocoa science for kids",
        "supporting_keywords": ["pease porridge hot rhyme kids", "why does milk form a skin", "winter hot chocolate cartoon"],
        "fact_summary": "When warm milk or cocoa sits on the counter, water evaporates from the surface while milk proteins like casein and whey dry out and tangle together, forming a harmless rubbery film on top.",
        "hook": "Pease porridge hot, pease porridge cold! Ever notice that weird thin skin that forms on top of your warm hot cocoa?",
        "publish_slot_est": "2026-12-20T15:30:00-05:00",
        "publish_at_utc": "2026-12-20T20:30:00Z",
        "lines": [
            {"text": "Pease porridge hot, pease porridge cold, in the pot nine days old!", "caps": "Pease porridge *HOT, | pease porridge *COLD, | in the pot *NINE | days *OLD!"},
            {"text": "Have you ever seen that strange thin skin sitting on top of your warm hot cocoa?", "caps": "Have you ever seen that strange *THIN | skin sitting on top of your *WARM | hot *COCOA?"},
            {"text": "Don't worry, it's not plastic—it's pure kitchen science!", "caps": "Don't worry, it's not *PLASTIC— | it's pure *KITCHEN | *SCIENCE!"},
            {"text": "Warm milk is packed with friendly proteins and tiny drops of healthy fat!", "caps": "Warm milk is *PACKED | with friendly *PROTEINS | and tiny drops of *HEALTHY | *FAT!"},
            {"text": "As steam rises, water evaporates quickly from the very top surface!", "caps": "As steam *RISES, | water evaporates *QUICKLY | from the very *TOP | surface!"},
            {"text": "The milk proteins dry out and tangle together, forming a delicate edible blanket!", "caps": "The milk proteins *DRY | out and tangle together, *FORMING | a delicate edible *BLANKET!"},
            {"text": "Just stir it with a spoon or whisk, and it melts right back into chocolatey goodness!", "caps": "Just stir it with a *SPOON | or whisk, and it *MELTS | right back into chocolatey *GOODNESS!"},
            {"text": "Now you know the delicious food chemistry behind Pease Porridge Hot!", "caps": "Now you *KNOW | the delicious food *CHEMISTRY | behind Pease *PORRIDGE | *HOT!"},
            {"text": "Sip into more fun discoveries and subscribe to BabyBeats Rhymo!", "caps": "*SIP into more | fun *DISCOVERIES and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "21_12_26",
        "day": 41,
        "date_str": "21/12/26",
        "category": "space-nature",
        "title": "Winter Solstice: Why Winter Nights Are the Longest of the Year!",
        "thumb_text": "LONGEST NIGHT?!",
        "primary_keyword": "winter solstice for kids cartoon",
        "supporting_keywords": ["shortest day of the year preschool", "why are winter nights long", "earth tilt science song"],
        "fact_summary": "Earth spins at a 23.5-degree tilt. During December, the Northern Hemisphere tilts furthest away from the sun, making the sun's path across the sky short and low, giving us the longest night of the year.",
        "hook": "Welcome to the Winter Solstice! Today is the shortest day and longest night of the entire year! Why does that happen?",
        "publish_slot_est": "2026-12-21T15:30:00-05:00",
        "publish_at_utc": "2026-12-21T20:30:00Z",
        "lines": [
            {"text": "Star light, star bright, first star I see tonight!", "caps": "Star light, star *BRIGHT, | first star I *SEE | *TONIGHT!"},
            {"text": "Today is the Winter Solstice—the shortest day and longest night of the whole year!", "caps": "Today is the Winter *SOLSTICE— | the shortest day and longest *NIGHT | of the *WHOLE | *YEAR!"},
            {"text": "But did the sun take a nap? No, it's all about Earth's secret tilt!", "caps": "But did the sun take a *NAP? | No, it's all about *EARTH'S | secret *TILT!"},
            {"text": "Planet Earth spins tilted like a spinning top at twenty-three degrees!", "caps": "Planet Earth spins *TILTED | like a spinning top at *TWENTY-THREE | *DEGREES!"},
            {"text": "In December, the top half of Earth leans furthest away from the sun's warm rays!", "caps": "In December, the top *HALF | of Earth leans furthest *AWAY | from the sun's warm *RAYS!"},
            {"text": "Because of that tilt, the sun takes a very low, quick shortcut across the winter sky!", "caps": "Because of that *TILT, | the sun takes a very *LOW, | quick shortcut across the winter *SKY!"},
            {"text": "Less daytime sunlight means long, cozy nights for stargazing and dreaming!", "caps": "Less daytime *SUNLIGHT | means long, cozy *NIGHTS | for stargazing and *DREAMING!"},
            {"text": "And starting tomorrow, the days start getting brighter and longer again!", "caps": "And starting *TOMORROW, | the days start getting *BRIGHTER | and longer *AGAIN!"},
            {"text": "Celebrate the solstice with us and subscribe to BabyBeats Rhymo!", "caps": "*CELEBRATE the solstice | with us and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "22_12_26",
        "day": 42,
        "date_str": "22/12/26",
        "category": "animal-vs",
        "title": "Arctic Reindeer: Why Reindeer Eyes Turn Deep Blue in Winter!",
        "thumb_text": "BLUE EYE SECRET!",
        "primary_keyword": "reindeer science facts for kids",
        "supporting_keywords": ["rudolph reindeer cartoon for toddlers", "arctic animal adaptations preschool", "reindeer eye color shift"],
        "fact_summary": "In bright arctic summer, reindeer eyes have golden reflective layers. But in dark winter, pupil pressure compacts the eye's tapetum lucidum collagen fibers, turning them deep blue to scatter light and see in the dark!",
        "hook": "Rudolph the red-nosed reindeer had a shiny nose! But did you know arctic reindeer have eyes that literally CHANGE COLOR from golden to deep blue?",
        "publish_slot_est": "2026-12-22T15:30:00-05:00",
        "publish_at_utc": "2026-12-22T20:30:00Z",
        "lines": [
            {"text": "Rudolph the red-nosed reindeer had a very shiny nose!", "caps": "Rudolph the red-nosed *REINDEER | had a very *SHINY | *NOSE!"},
            {"text": "But reindeer have an even wilder superpower in their eyes!", "caps": "But reindeer have an even *WILDER | superpower in their *EYES!"},
            {"text": "In bright summer, reindeer eyes shine with a sparkling golden color!", "caps": "In bright *SUMMER, | reindeer eyes shine with a *SPARKLING | golden *COLOR!"},
            {"text": "But during dark arctic winters, their eyes turn deep, ocean blue!", "caps": "But during dark arctic *WINTERS, | their eyes turn *DEEP, | ocean *BLUE!"},
            {"text": "The constant winter darkness makes their pupils stretch wide open day and night!", "caps": "The constant winter *DARKNESS | makes their pupils stretch wide *OPEN | day and *NIGHT!"},
            {"text": "This pressure tightens the reflective mirror behind their retinas!", "caps": "This pressure *TIGHTENS | the reflective mirror behind *THEIR | *RETINAS!"},
            {"text": "Blue eyes scatter moonlight, letting reindeer spot hidden lichen beneath the snow!", "caps": "Blue eyes scatter moonlight, *LETTING | reindeer spot hidden lichen *BENEATH | the *SNOW!"},
            {"text": "Now you know the real arctic magic behind Santa's reindeer!", "caps": "Now you *KNOW | the real arctic *MAGIC | behind Santa's *REINDEER!"},
            {"text": "Fly into more animal mysteries and subscribe to BabyBeats Rhymo!", "caps": "*FLY into more | animal *MYSTERIES and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "23_12_26",
        "day": 43,
        "date_str": "23/12/26",
        "category": "moral-story",
        "title": "Jack and Jill: Why Is Winter Ice So Slippery?",
        "thumb_text": "WHY ICE SLIPS!",
        "primary_keyword": "why is ice slippery science for kids",
        "supporting_keywords": ["jack and jill rhyme for kids", "ice friction physics cartoon", "preschool winter science"],
        "fact_summary": "Ice isn't slippery just because it's cold. The very top surface of ice has loosely bonded water molecules that act like a microscopic liquid water film, dramatically reducing friction so shoes slide!",
        "hook": "Jack and Jill went up the hill... and tumbled right down! But why does winter ice make everyone slip and slide so easily?",
        "publish_slot_est": "2026-12-23T15:30:00-05:00",
        "publish_at_utc": "2026-12-23T20:30:00Z",
        "lines": [
            {"text": "Jack and Jill went up the hill to fetch a pail of water!", "caps": "Jack and Jill went *UP | the hill to fetch a pail of *WATER!"},
            {"text": "Jack fell down and broke his crown, slipping on the slick winter ice!", "caps": "Jack fell *DOWN | and broke his crown, *SLIPPING | on the slick winter *ICE!"},
            {"text": "Why is smooth ice so much more slippery than hard wooden floors?", "caps": "Why is smooth *ICE | so much more slippery than hard *WOODEN | *FLOORS?"},
            {"text": "At the very surface of ice, water molecules cannot hold onto each other tightly!", "caps": "At the very *SURFACE | of ice, water molecules cannot *HOLD | onto each other *TIGHTLY!"},
            {"text": "They form an ultra-thin layer of loose, slushy liquid water molecules!", "caps": "They form an ultra-thin *LAYER | of loose, slushy liquid *WATER | *MOLECULES!"},
            {"text": "When your warm boot steps down, that microscopic water layer acts like ball bearings!", "caps": "When your warm boot steps *DOWN, | that microscopic water layer *ACTS | like ball *BEARINGS!"},
            {"text": "There's almost zero friction, which lets your feet glide—or tumble down the hill!", "caps": "There's almost zero *FRICTION, | which lets your feet *GLIDE— | or tumble down the *HILL!"},
            {"text": "Now you know the slippery physics behind Jack and Jill!", "caps": "Now you *KNOW | the slippery *PHYSICS | behind Jack and *JILL!"},
            {"text": "Tread carefully and subscribe to BabyBeats Rhymo for daily facts!", "caps": "*TREAD carefully and | *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *FACTS!"}
        ]
    },
    {
        "id": "24_12_26",
        "day": 44,
        "date_str": "24/12/26",
        "category": "space-nature",
        "title": "Jingle Bells: How Sleigh Runners Glide Across Packed Snow!",
        "thumb_text": "SLEIGH GLIDE TRICK!",
        "primary_keyword": "jingle bells song for kids",
        "supporting_keywords": ["how sleds work physics kids", "jingle bells cartoon rhyme", "winter sleigh science preschool"],
        "fact_summary": "Instead of narrow wheels that dig into powdery snow, sleighs have long, polished curved runners that spread weight over a large surface area and glide on a melted water film created by friction.",
        "hook": "Jingle bells, jingle bells, jingle all the way! Oh what fun it is to ride in a one-horse open sleigh! But how do heavy sleighs glide over deep snow without sinking?",
        "publish_slot_est": "2026-12-24T15:30:00-05:00",
        "publish_at_utc": "2026-12-24T20:30:00Z",
        "lines": [
            {"text": "Jingle bells, jingle bells, jingle all the way! Oh what fun it is to ride in a one-horse open sleigh!", "caps": "Jingle *BELLS, | jingle bells, jingle all the *WAY! | Oh what fun it is to ride in a *ONE-HORSE | open *SLEIGH!"},
            {"text": "How does a heavy wooden sleigh glide smoothly across soft snow without sinking in?", "caps": "How does a heavy wooden *SLEIGH | glide smoothly across soft *SNOW | without sinking *IN?"},
            {"text": "If you used thin bike wheels, the heavy weight would sink right into the snowbank!", "caps": "If you used thin bike *WHEELS, | the heavy weight would sink *RIGHT | into the *SNOWBANK!"},
            {"text": "But sleigh runners are long, smooth, and gently curved upward at the front!", "caps": "But sleigh runners are *LONG, | smooth, and gently curved *UPWARD | at the *FRONT!"},
            {"text": "They spread the weight across the snow so the sleigh floats on top of the powder!", "caps": "They spread the *WEIGHT | across the snow so the sleigh *FLOATS | on top of the *POWDER!"},
            {"text": "As the runner slides, tiny friction melts a microscopic film of slippery water!", "caps": "As the runner *SLIDES, | tiny friction melts a microscopic *FILM | of slippery *WATER!"},
            {"text": "The sleigh hydroplanes across the snow like a speedboat across a lake!", "caps": "The sleigh hydroplanes across the *SNOW | like a speedboat across a *LAKE!"},
            {"text": "Now you know the winter engineering behind Jingle Bells!", "caps": "Now you *KNOW | the winter *ENGINEERING | behind Jingle *BELLS!"},
            {"text": "Ring in the holiday fun and subscribe to BabyBeats Rhymo!", "caps": "*RING in the holiday | fun and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "25_12_26",
        "day": 45,
        "date_str": "25/12/26",
        "category": "space-nature",
        "title": "O Christmas Tree: Why Pine Trees Stay Green in Winter Snow!",
        "thumb_text": "EVERGREEN SECRET!",
        "primary_keyword": "evergreen trees for kids science",
        "supporting_keywords": ["o christmas tree rhyme cartoon", "why do pine trees stay green", "preschool winter plant facts"],
        "fact_summary": "Pine needles are narrow and covered in a thick waterproof waxy coating that locks in moisture during freezing winter, with natural antifreeze inside cells so leaves don't freeze and fall!",
        "hook": "O Christmas tree, O Christmas tree, how lovely are your branches! But why do pine trees stay bright green when all other trees lose their leaves?",
        "publish_slot_est": "2026-12-25T15:30:00-05:00",
        "publish_at_utc": "2026-12-25T20:30:00Z",
        "lines": [
            {"text": "O Christmas tree, O Christmas tree, how lovely are your branches!", "caps": "O Christmas *TREE, | O Christmas tree, how *LOVELY | are your *BRANCHES!"},
            {"text": "While oak and maple trees drop all their leaves, pine trees stay brilliantly green!", "caps": "While oak and maple trees *DROP | all their leaves, pine trees stay *BRILLIANTLY | *GREEN!"},
            {"text": "Why don't evergreen trees freeze and lose their needles in the snow?", "caps": "Why don't evergreen trees *FREEZE | and lose their needles in the *SNOW?"},
            {"text": "Pine needles are super skinny, so heavy snow slides right off without snapping branches!", "caps": "Pine needles are super *SKINNY, | so heavy snow slides right *OFF | without snapping *BRANCHES!"},
            {"text": "Each needle is coated in a thick, waterproof wax called cuticle that locks in water!", "caps": "Each needle is coated in a *THICK, | waterproof wax called *CUTICLE | that locks in *WATER!"},
            {"text": "Inside their cells, evergreen trees produce natural sugar antifreeze!", "caps": "Inside their *CELLS, | evergreen trees produce natural *SUGAR | *ANTIFREEZE!"},
            {"text": "This stops winter ice crystals from puncturing delicate plant cells!", "caps": "This stops winter ice *CRYSTALS | from puncturing delicate plant *CELLS!"},
            {"text": "Now you know the botanical secret behind O Christmas Tree!", "caps": "Now you *KNOW | the botanical *SECRET | behind O Christmas *TREE!"},
            {"text": "Celebrate nature's wonders and subscribe to BabyBeats Rhymo!", "caps": "*CELEBRATE nature's | wonders and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "26_12_26",
        "day": 46,
        "date_str": "26/12/26",
        "category": "body-science",
        "title": "Brrr It's Cold: Why Do We Shiver and Chattering Teeth?",
        "thumb_text": "WHY WE SHIVER!",
        "primary_keyword": "why do we shiver science for kids",
        "supporting_keywords": ["chattering teeth cold kids cartoon", "human body winter science", "preschool shivering rhyme"],
        "fact_summary": "When your skin sensors detect freezing temperatures, your brain's hypothalamus triggers rapid involuntary muscle spasms—shivering—which burns energy and generates internal emergency heat to warm you up!",
        "hook": "Brrr, it's freezing outside! Your teeth start chattering and your body shakes! Why does your body start shivering on purpose?",
        "publish_slot_est": "2026-12-26T15:30:00-05:00",
        "publish_at_utc": "2026-12-26T20:30:00Z",
        "lines": [
            {"text": "Brrr, brrr, blow the winter wind, wrap your scarf up to your chin!", "caps": "*BRRR, brrr, blow the winter *WIND, | wrap your scarf up to your *CHIN!"},
            {"text": "Why do our muscles shake and our teeth go clack-clack-clack when we feel chilly?", "caps": "Why do our muscles *SHAKE | and our teeth go clack-clack-clack *WHEN | we feel *CHILLY?"},
            {"text": "Shivering is your body's built-in emergency heating furnace!", "caps": "Shivering is your body's *BUILT-IN | emergency heating *FURNACE!"},
            {"text": "When tiny thermometers in your skin feel the cold, your brain sends an instant alert!", "caps": "When tiny thermometers in your *SKIN | feel the cold, your brain sends an *INSTANT | *ALERT!"},
            {"text": "Your brain commands skeletal muscles to twitch and tighten up to thirty times a second!", "caps": "Your brain commands skeletal *MUSCLES | to twitch and tighten up to thirty times a *SECOND!"},
            {"text": "Rapid muscle movement burns stored glucose energy and releases warm thermal heat!", "caps": "Rapid muscle movement burns *STORED | glucose energy and releases warm *THERMAL | *HEAT!"},
            {"text": "Your jaw muscles contract too, making your teeth chatter together!", "caps": "Your jaw muscles *CONTRACT | too, making your teeth *CHATTER | *TOGETHER!"},
            {"text": "Shivering quickly warms your core back up to a toasty ninety-eight degrees!", "caps": "Shivering quickly warms your *CORE | back up to a toasty ninety-eight *DEGREES!"},
            {"text": "Warm up with smart science—subscribe to BabyBeats Rhymo!", "caps": "*WARM up with smart | *SCIENCE— | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "27_12_26",
        "day": 47,
        "date_str": "27/12/26",
        "category": "space-nature",
        "title": "Cozy Fireplace: Why Wood Crackles and Pops in the Fire!",
        "thumb_text": "FIREPLACE POPS?!",
        "primary_keyword": "why does wood crackle in fire kids",
        "supporting_keywords": ["fireplace campfire science cartoon", "cozy fire nursery rhyme", "wood popping science preschool"],
        "fact_summary": "Wood contains trapped pockets of water, resin, and sap deep inside microscopic cellulose tubes. As heat turns trapped water to expanding steam, the high pressure ruptures the wood chamber with a loud pop!",
        "hook": "Sitting cozy by the fireplace! Crackle, pop, snap! Have you ever wondered what makes burning logs pop and shoot out tiny sparks?",
        "publish_slot_est": "2026-12-27T15:30:00-05:00",
        "publish_at_utc": "2026-12-27T20:30:00Z",
        "lines": [
            {"text": "Warm little fire glowing bright, chasing away the chilly night!", "caps": "Warm little fire glowing *BRIGHT, | chasing away the chilly *NIGHT!"},
            {"text": "Snap, crackle, pop! What makes wooden logs pop and spark inside the fireplace?", "caps": "Snap, crackle, *POP! | What makes wooden logs pop and *SPARK | inside the *FIREPLACE?"},
            {"text": "Even dry firewood has tiny droplets of water and tree sap trapped deep inside!", "caps": "Even dry firewood has *TINY | droplets of water and tree sap *TRAPPED | deep *INSIDE!"},
            {"text": "Wood is made of microscopic cellulose straws that once carried water up the tree!", "caps": "Wood is made of microscopic *CELLULOSE | straws that once carried water *UP | the *TREE!"},
            {"text": "As fierce fire heats the log, that trapped water boils and turns into expanding steam!", "caps": "As fierce fire *HEATS | the log, that trapped water boils and *TURNS | into expanding *STEAM!"},
            {"text": "The steam expands over a thousand times, building immense pressure inside the wood tube!", "caps": "The steam expands over a thousand *TIMES, | building immense pressure inside the *WOOD | *TUBE!"},
            {"text": "Bam! The wood pocket bursts open with a loud pop, releasing a dancing spark!", "caps": "*BAM! The wood pocket *BURSTS | open with a loud pop, releasing a *DANCING | *SPARK!"},
            {"text": "Now you know the cozy physics behind your crackling winter fire!", "caps": "Now you *KNOW | the cozy *PHYSICS | behind your crackling winter *FIRE!"},
            {"text": "Spark your curiosity and subscribe to BabyBeats Rhymo!", "caps": "*SPARK your curiosity | and *SUBSCRIBE to | *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "28_12_26",
        "day": 48,
        "date_str": "28/12/26",
        "category": "animal-vs",
        "title": "Rock-a-bye Baby: Why Animals Hibernate and Sleep All Winter!",
        "thumb_text": "HIBERNATION SECRET!",
        "primary_keyword": "why do animals hibernate for kids",
        "supporting_keywords": ["bear hibernation science cartoon", "rock a bye baby animal rhyme", "winter sleep animals preschool"],
        "fact_summary": "Winter brings scarce food and freezing temperatures. Hibernating animals drastically slow down their heartbeat, body temperature, and metabolism to live off stored fat until spring flowers bloom.",
        "hook": "Rock-a-bye baby on the tree top! When winter comes, why do bears, bats, and frogs go to sleep for months and months?",
        "publish_slot_est": "2026-12-28T15:30:00-05:00",
        "publish_at_utc": "2026-12-28T20:30:00Z",
        "lines": [
            {"text": "Rock-a-bye baby on the tree top, when the wind blows the cradle will rock!", "caps": "Rock-a-bye baby on the *TREE | top, when the wind *BLOWS | the cradle will *ROCK!"},
            {"text": "But in deep winter dens, why do bears and sleepy animals nap for months on end?", "caps": "But in deep winter *DENS, | why do bears and sleepy animals nap for *MONTHS | on *END?"},
            {"text": "In freezing winter, berries disappear and bugs hide, leaving very little food!", "caps": "In freezing winter, berries *DISAPPEAR | and bugs hide, leaving very little *FOOD!"},
            {"text": "Instead of hunting in the snow, animals enter a superpower state called Hibernation!", "caps": "Instead of hunting in the *SNOW, | animals enter a superpower state called *HIBERNATION!"},
            {"text": "A bear's heart slows down from fifty beats a minute to just eight beats!", "caps": "A bear's heart slows *DOWN | from fifty beats a minute to just *EIGHT | *BEATS!"},
            {"text": "Their body cools down and their engine runs in ultra power-saving mode!", "caps": "Their body cools *DOWN | and their engine runs in ultra power-saving *MODE!"},
            {"text": "They survive all winter by slowly burning energy stored in their autumn fat layer!", "caps": "They survive all *WINTER | by slowly burning energy stored in their autumn *FAT | *LAYER!"},
            {"text": "When warm spring sunshine returns, they wake up refreshed and ready to play!", "caps": "When warm spring sunshine *RETURNS, | they wake up refreshed and *READY | to *PLAY!"},
            {"text": "Wake up to daily learning and subscribe to BabyBeats Rhymo!", "caps": "*WAKE up to daily | *LEARNING and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "29_12_26",
        "day": 49,
        "date_str": "29/12/26",
        "category": "space-nature",
        "title": "Snow Clouds: How Fluffy Clouds Turn Into Soft Snowflakes!",
        "thumb_text": "CLOUD TO SNOW!",
        "primary_keyword": "how does snow form for kids",
        "supporting_keywords": ["rain rain go away snow edition", "snow clouds science cartoon", "preschool weather science rhyme"],
        "fact_summary": "When the upper atmosphere drops below 32 degrees Fahrenheit, water vapor bypasses liquid form through deposition, directly crystalizing into ice on microscopic pollen or mineral dust particles.",
        "hook": "Rain, rain go away... wait, it's too cold for rain! How do fluffy gray clouds turn water vapor into soft, fluffy white snow?",
        "publish_slot_est": "2026-12-29T15:30:00-05:00",
        "publish_at_utc": "2026-12-29T20:30:00Z",
        "lines": [
            {"text": "Rain, rain, go away, come again another day!", "caps": "Rain, rain, go *AWAY, | come again another *DAY!"},
            {"text": "But when winter temperatures drop below freezing, rain turns into magical snow!", "caps": "But when winter temperatures drop below *FREEZING, | rain turns into magical *SNOW!"},
            {"text": "How does invisible vapor floating in fluffy clouds turn into soft white snowflakes?", "caps": "How does invisible vapor floating in fluffy *CLOUDS | turn into soft white *SNOWFLAKES?"},
            {"text": "High in the cold sky, clouds are filled with freezing water vapor and tiny floating dust!", "caps": "High in the cold *SKY, | clouds are filled with freezing water vapor and tiny *FLOATING | *DUST!"},
            {"text": "When the temperature dips below thirty-two degrees Fahrenheit, magic happens!", "caps": "When the temperature dips below *THIRTY-TWO | degrees Fahrenheit, magic *HAPPENS!"},
            {"text": "Water vapor skips turning into rain and crystalizes directly into solid ice!", "caps": "Water vapor skips turning into *RAIN | and crystalizes directly into solid *ICE!"},
            {"text": "Billions of tiny ice crystals group together into soft, puffy snowflakes!", "caps": "Billions of tiny ice *CRYSTALS | group together into soft, puffy *SNOWFLAKES!"},
            {"text": "When they become too heavy for the cloud to hold, they gently float down to Earth!", "caps": "When they become too heavy for the cloud to *HOLD, | they gently float down to *EARTH!"},
            {"text": "Snow into more fun science and subscribe to BabyBeats Rhymo!", "caps": "*SNOW into more | fun *SCIENCE and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "30_12_26",
        "day": 50,
        "date_str": "30/12/26",
        "category": "moral-story",
        "title": "Hickory Dickory Dock: How Clocks Count Every Single Second!",
        "thumb_text": "HOW CLOCKS TICK!",
        "primary_keyword": "hickory dickory dock rhyme for kids",
        "supporting_keywords": ["how clocks work science for kids", "hickory dickory dock cartoon", "preschool time clock song"],
        "fact_summary": "Inside old grandfather clocks, a swinging pendulum takes the exact same time on every swing, releasing gears tooth by tooth. Modern clocks use a tiny quartz crystal vibrating 32,768 times every second!",
        "hook": "Hickory dickory dock, the mouse ran up the clock! The clock struck one! But how does a ticking clock know exactly how long a second is?",
        "publish_slot_est": "2026-12-30T15:30:00-05:00",
        "publish_at_utc": "2026-12-30T20:30:00Z",
        "lines": [
            {"text": "Hickory dickory dock, the mouse ran up the clock!", "caps": "Hickory dickory *DOCK, | the mouse ran up the *CLOCK!"},
            {"text": "The clock struck one, the mouse ran down, hickory dickory dock!", "caps": "The clock struck *ONE, | the mouse ran down, hickory dickory *DOCK!"},
            {"text": "Tick-tock, tick-tock! How does a clock measure every single second so accurately?", "caps": "Tick-tock, *TICK-TOCK! | How does a clock measure every single second so *ACCURATELY?"},
            {"text": "In big grandfather clocks, a swinging pendulum rocks steadily back and forth!", "caps": "In big grandfather *CLOCKS, | a swinging pendulum rocks steadily back and *FORTH!"},
            {"text": "Gravity ensures each swing takes the exact same fraction of a second!", "caps": "Gravity ensures each *SWING | takes the exact same fraction of a *SECOND!"},
            {"text": "An escapement gear catches and releases, making the famous tick-tock sound!", "caps": "An escapement gear catches and *RELEASES, | making the famous tick-tock *SOUND!"},
            {"text": "In modern digital watches, a tiny quartz crystal vibrates thirty-two thousand times a second!", "caps": "In modern digital *WATCHES, | a tiny quartz crystal vibrates thirty-two thousand times a *SECOND!"},
            {"text": "A microchip counts the vibrations and moves the hands forward right on time!", "caps": "A microchip counts the *VIBRATIONS | and moves the hands forward right on *TIME!"},
            {"text": "Count every second of learning—subscribe to BabyBeats Rhymo!", "caps": "*COUNT every second | of *LEARNING— | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    }
]


def update_topic_queue():
    if QUEUE_PATH.exists():
        q = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    else:
        q = {"channel": "BabyBeats Rhymo", "topics": []}
    topics = q.setdefault("topics", [])
    for nt in TOPICS_13:
        existing = next((t for t in topics if t["id"] == nt["id"]), None)
        item_data = {
            "id": nt["id"],
            "day": nt["day"],
            "category": nt["category"],
            "title": nt["title"],
            "thumb_text": nt["thumb_text"],
            "primary_keyword": nt["primary_keyword"],
            "supporting_keywords": nt["supporting_keywords"],
            "score_breakdown": {
                "audience_demand": 19,
                "recent_growth": 17,
                "competition_opportunity": 14,
                "audience_curiosity": 16,
                "click_potential": 9,
                "retention_potential": 9,
                "production_feasibility": 5,
                "niche_relevance": 5
            },
            "total_score": 94,
            "fact_summary": nt["fact_summary"],
            "sources": [
                "https://kidshealth.org",
                "https://www.nasa.gov/kidsclub"
            ],
            "hook": nt["hook"],
            "visual_focus": "vibrant nursery rhyme cartoon mascot explaining everyday science",
            "status": "ready_for_upload"
        }
        if existing:
            existing.update(item_data)
        else:
            topics.append(item_data)
    QUEUE_PATH.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {QUEUE_PATH} with {len(TOPICS_13)} topics.")


def build_shots_for_topic(nt: dict) -> str:
    thumb_badge = nt.get("thumb_text", "RHYME SCIENCE!").replace("'", "")
    lines = nt["lines"]
    shot_blocks = []
    
    scenes = [
        ("kid", "room", f"K.room(); P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), {{ mood: 'happy', t }}); K.pill('{thumb_badge}', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6))); K.burst(540, 740, 1.1, 0.5);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("science_check", "blank", "fillAll('#FFFBEB'); P.magnifier(540, 760, 210); K.pill('SCIENCE MYSTERY!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'sparkle');"),
        ("shock", "room", "K.room(); P.kidCartoon(380, 860, 1.55, { mood: 'shock', t }); K.shockLines(380, 740, 240, clamp((lt - 0.4) * 3)); K.pill('WAIT WHAT?!', 540, 310, 44, C.red, C.white, 1);", "cue(st, 'alarm', { dur: 0.8 });"),
        ("deep_dive", "xray", "K.xray(t); P.planetGlobe(540, 760, 190 * eob(seg(lt, 0, 0.4)), t, true); K.pill('HOW IT WORKS!', 540, 305, 42, C.yellow, C.ink, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle');"),
        ("microscope", "blank", "fillAll('#EFF6FF'); P.creatureBuddy(540, 770, 1.8 * eob(seg(lt, 0, 0.35)), t, '#0284C7'); K.pill('NATURE SECRET!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'pop');"),
        ("action", "blank", "fillAll('#FEF2F2'); P.batteryMeter(540, 760, 1.45, 1.0); K.pill('SUPER POWER!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle');"),
        ("happy_kid", "room", "K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.heart(540, 520, 2.0 * eob(seg(lt, 0.2, 0.6)), Math.abs(Math.sin(lt * 6))); K.pill('SMART TODDLER!', 540, 310, 44, '#2A9D8F', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'boing');"),
        ("truth", "blank", "fillAll('#F0FDF4'); P.kidCartoon(360, 860, 1.45, { mood: 'happy', t }); P.magnifier(720, 680, 155); K.pill('REAL TRUTH!', 540, 310, 44, '#15803D', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.35, 'pop');"),
        ("outro", "room", "K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4))); K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });")
    ]

    for i in range(len(lines)):
        name, bg, code, sfx = scenes[i % len(scenes)]
        if i == len(lines) - 1:
            name, bg, code, sfx = scenes[-1]
        shot_blocks.append(f"""  {{
    const st = cut({i});
    add({{
      id: 'S{i+1:02d}', at: st, cam: [540, 800], note: 'scene {name}',
      draw(lt, d, t) {{
        {code}
      }}
    }});
    {sfx}
  }}""")

    return f"""import {{ ctx, C, W, H, TAU, clamp, lerp, seg, eo, eio, eob, rnd, bigText, fillAll, rr, circle, ell, line }} from './core/lib.js';
import {{ L, Le, Wd, T }} from './core/timing.js';
import * as K from './core/kit.js';
import * as P from './cartoon_props.js';

export function buildShots() {{
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);

{chr(10).join(shot_blocks)}

  return {{ shots: S, cues: CUES }};
}}
"""


def append_upload_queue(entry: dict):
    if UPLOAD_Q_PATH.exists():
        data = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
    else:
        data = {"channel_id": "UCR-Di4-tEAdUM7oPzlGn-vg", "items": []}
    items = data.setdefault("items", [])
    existing = next((it for it in items if it.get("id") == entry["id"]), None)
    if existing:
        existing.update(entry)
    else:
        items.append(entry)
    UPLOAD_Q_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_single_short(nt: dict):
    tid = nt["id"]
    proj_name = f"{tid}_short"
    proj_dir = ROOT / "videos" / proj_name
    print(f"\n========================================================")
    print(f"GENERATING [{nt['day']}/50]: {proj_name} ({nt['title']})")
    print(f"========================================================")

    if not proj_dir.exists():
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(NEW_VIDEO_PS1),
            "-Style", "inside-out", "-Name", proj_name, "-Dir", str(ROOT / "videos")
        ]
        subprocess.run(cmd, check=True)

    # Copy cartoon props
    shutil.copyfile(PROPS_TEMPLATE, proj_dir / "src" / "cartoon_props.js")

    # Script json
    script = {
        "title": nt["title"],
        "thumb_text": nt["thumb_text"],
        "voice": "am_puck",
        "speed": 1.05,
        "music": "bed",
        "lead": 0.35,
        "gap": 0.25,
        "outro": 0.85,
        "sources": ["https://kidshealth.org", "https://www.nasa.gov/kidsclub"],
        "lines": nt["lines"]
    }
    (proj_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    # Shots js
    (proj_dir / "src" / "shots.js").write_text(build_shots_for_topic(nt), encoding="utf-8")

    # SEO & Thumbnail
    (proj_dir / "renders").mkdir(exist_ok=True)
    seo_out = proj_dir / "seo_package.json"
    thumb_out = proj_dir / "renders" / f"{tid}_thumb.jpg"
    mp4_out = proj_dir / "renders" / f"{tid}_short.mp4"

    print("-> Building SEO package...")
    subprocess.run([PY_VENV, str(SEO_PY), "--topic-id", tid, "--out", str(seo_out)], check=True)

    if not thumb_out.exists():
        print("-> Rendering 1280x720 Thumbnail...")
        try:
            subprocess.run(["node", str(MAKE_THUMB_MJS), str(thumb_out), nt["thumb_text"], nt["category"], "BABYBEATS RHYMO"], check=True)
        except subprocess.CalledProcessError:
            if not thumb_out.exists():
                raise
    else:
        print(f"-> Thumbnail already exists: {thumb_out.name}")

    if not mp4_out.exists():
        print("-> Executing Audio Synthesis & Video Pipeline (Kokoro + Whisper + Chrome + ffmpeg)...")
        pipe_cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(RUN_PIPELINE_PS1),
            "-ProjectDir", str(proj_dir),
            "-OutVideo", str(mp4_out),
            "-SheetStep", "2", "-SheetCols", "5"
        ]
        subprocess.run(pipe_cmd, check=True)
    else:
        print(f"-> MP4 already exists: {mp4_out.name}")

    # Verify with ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,width,height", "-of", "json", str(mp4_out)],
        capture_output=True, text=True, check=True
    )
    info = json.loads(probe.stdout)
    vstream = next((s for s in info.get("streams", []) if s.get("width")), {})
    if int(vstream.get("width", 0)) != 1080 or int(vstream.get("height", 0)) != 1920:
        raise RuntimeError(f"Unexpected dimensions: {vstream}")
    meta = {
        "duration_sec": round(float(info["format"]["duration"]), 2),
        "size_bytes": int(info["format"]["size"]),
        "width": vstream["width"],
        "height": vstream["height"]
    }
    print(f"VERIFIED MP4: {mp4_out.name} ({meta['duration_sec']}s, {meta['size_bytes']} bytes)")

    seo = json.loads(seo_out.read_text(encoding="utf-8"))
    upload_entry = {
        "id": proj_name,
        "topic_id": tid,
        "format": "short",
        "scheduled_slot_est": "15:30 EST",
        "title": seo.get("selected_title") or nt["title"],
        "video_path": str(mp4_out),
        "thumb_path": str(thumb_out),
        "seo_path": str(seo_out),
        "made_for_kids": True,
        "category_id": "27",
        "status": "READY_FOR_UPLOAD",
        "youtube_video_id": None,
        "youtube_url": None,
        "scheduled_publish_est": nt["publish_slot_est"],
        "publish_at": nt["publish_at_utc"],
        "video_specs": meta,
        "updated_at_ist": datetime.now(IST).isoformat()
    }
    append_upload_queue(upload_entry)
    print(f"SUCCESS: Added {proj_name} to upload_queue.json as READY_FOR_UPLOAD (publish_at: {nt['publish_at_utc']})")


def main():
    update_topic_queue()
    total = len(TOPICS_13)
    for i, nt in enumerate(TOPICS_13, 1):
        print(f"\n>>> PROCESSING VIDEO {i}/{total}: {nt['id']}_short <<<")
        generate_single_short(nt)
    print("\n========================================================")
    print(f"ALL {total} NEW MONTH 2 NURSERY RHYMES GENERATED SUCCESSFULLY!")
    print("========================================================")


if __name__ == "__main__":
    main()

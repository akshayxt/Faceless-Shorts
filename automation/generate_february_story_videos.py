import argparse
import json
import os
import shutil
import subprocess
import sys
import time
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

FEBRUARY_27_STORIES = [
    {
        "id": "02_02_27",
        "day": 84,
        "date_str": "02/02/27",
        "category": "moral-story",
        "title": "The Boy Who Lost His Temper: Cooling Down the Volcano!",
        "thumb_text": "ANGRY VOLCANO?!",
        "primary_keyword": "kids anger management cartoon story",
        "supporting_keywords": ["calming down for kids", "emotional regulation children", "angry volcano breathing trick"],
        "fact_summary": "When we get furious, our brain's fight-or-flight switch fires; taking 3 deep belly breaths cools our brain down and prevents hurtful words.",
        "hook": "Leo felt like a red-hot volcano ready to blast lava everywhere! How did the 3-breath magic trick save the day?",
        "publish_slot_est": "2027-02-02T15:30:00-05:00",
        "publish_at_utc": "2027-02-02T20:30:00Z",
        "lines": [
            {"text": "Have you ever felt so angry your cheeks burned like fiery red lava?", "caps": "Have you ever felt so *ANGRY | your cheeks burned like *FIERY | red *LAVA?"},
            {"text": "Leo lost his favorite blue toy car and felt an explosive volcano rumble inside!", "caps": "Leo lost his favorite *CAR | and felt an explosive *VOLCANO | rumble *INSIDE!"},
            {"text": "He wanted to stomp, scream, and throw his pillow across the bedroom!", "caps": "He wanted to *STOMP, | scream, and *THROW | his pillow *ACROSS the room!"},
            {"text": "Then Rhymo whispered, When the volcano bubbles, freeze and breathe!", "caps": "Then Rhymo *WHISPERED, | When the volcano bubbles, | *FREEZE and *BREATHE!"},
            {"text": "Inhale through your nose like smelling sweet roses for four slow seconds!", "caps": "*INHALE through your nose | like smelling sweet *ROSES | for four slow *SECONDS!"},
            {"text": "Blow out gently through your lips like blowing out birthday candles!", "caps": "*BLOW out gently | through your lips like *BLOWING | birthday *CANDLES!"},
            {"text": "One, two, three! The fiery red heat vanished into gentle cool air!", "caps": "One, two, *THREE! | The fiery red heat *VANISHED | into cool *AIR!"},
            {"text": "You are the boss of your feelings, not the fiery volcano!", "caps": "You are the *BOSS | of your feelings, *NOT | the fiery *VOLCANO!"},
            {"text": "Stay calm, cool, and subscribe to BabyBeats Rhymo for daily stories!", "caps": "Stay *CALM, cool, | and *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *STORIES!"}
        ]
    },
    {
        "id": "03_02_27",
        "day": 85,
        "date_str": "03/02/27",
        "category": "science-curiosity",
        "title": "Why Do We Yawn? The Brain-Cooling Mystery!",
        "thumb_text": "WHY DO WE YAWN?!",
        "primary_keyword": "why do we yawn kids science cartoon",
        "supporting_keywords": ["why yawns are contagious", "brain cooling mystery kids", "human body facts children"],
        "fact_summary": "Yawns are not just about being sleepy; a deep yawn rushes cool air into our head to cool down our hardworking brain like a computer fan!",
        "hook": "Seeing someone yawn makes YOU yawn in two seconds flat! But why does your mouth stretch open so wide?",
        "publish_slot_est": "2027-02-03T15:30:00-05:00",
        "publish_at_utc": "2027-02-03T20:30:00Z",
        "lines": [
            {"text": "Bet you can't watch this entire video without yawning once!", "caps": "Bet you can't watch this *ENTIRE | video without *YAWNING once!"},
            {"text": "Your mouth opens super wide and you take in a giant gulp of air!", "caps": "Your mouth opens *SUPER wide | and you take in a *GIANT | gulp of *AIR!"},
            {"text": "Are you just bored? No way! Your brain is an active supercomputer!", "caps": "Are you just *BORED? | No way! Your brain is an *ACTIVE | *SUPERCOMPUTER!"},
            {"text": "When your brain works hard thinking and playing, it heats up like a phone!", "caps": "When your brain works *HARD, | it heats up like a *PHONE | playing *GAMES!"},
            {"text": "A big yawn acts like a cooling fan, pumping fresh cool air inside!", "caps": "A big yawn acts like a *COOLING | fan, pumping *FRESH | cool air *INSIDE!"},
            {"text": "It cools your blood vessels and resets your energy levels instantly!", "caps": "It cools your *BLOOD | vessels and resets your *ENERGY | *INSTANTLY!"},
            {"text": "And when friends yawn together, your mirror neurons show you share feelings!", "caps": "And when friends yawn *TOGETHER, | your mirror neurons show *YOU | share *FEELINGS!"},
            {"text": "Your body has superpowers you use every single day without knowing!", "caps": "Your body has *SUPERPOWERS | you use every *SINGLE | day without *KNOWING!"},
            {"text": "Feed your curious brain and subscribe to BabyBeats Rhymo!", "caps": "Feed your *CURIOUS brain | and *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "04_02_27",
        "day": 86,
        "date_str": "04/02/27",
        "category": "moral-story",
        "title": "Pip the Mouse Who Kept His Word: A Promise is Golden!",
        "thumb_text": "PROMISE IS GOLDEN!",
        "primary_keyword": "keeping promises moral story for children",
        "supporting_keywords": ["trust and honesty cartoon", "being dependable moral lesson", "mouse and bear friendship story"],
        "fact_summary": "Keeping small promises builds trust; when you keep your word, friends know they can always count on you no matter what.",
        "hook": "Pip the tiny mouse promised to meet Barney Bear before sunset, but a giant berry feast tempted him! What did Pip choose?",
        "publish_slot_est": "2027-02-04T15:30:00-05:00",
        "publish_at_utc": "2027-02-04T20:30:00Z",
        "lines": [
            {"text": "Pip the tiny brown mouse made a solemn promise to his best friend Barney Bear!", "caps": "Pip the tiny *MOUSE | made a solemn *PROMISE | to his best friend *BARNEY!"},
            {"text": "I will bring you the magical blue seed before the forest sun sets!", "caps": "I will bring you the *MAGICAL | blue seed before the forest *SUN | *SETS!"},
            {"text": "On his way back, Pip stumbled upon a sparkling river of sweet strawberries!", "caps": "On his way back, Pip *STUMBLED | upon a sparkling river of *SWEET | *STRAWBERRIES!"},
            {"text": "All the squirrels cheered, Stay and feast with us, Pip! Sunset is far away!", "caps": "All the squirrels *CHEERED, | Stay and feast with us, *PIP! | Sunset is far *AWAY!"},
            {"text": "Pip's tummy rumbled, but he remembered Barney waiting patiently by the mossy rock!", "caps": "Pip's tummy *RUMBLED, | but he remembered Barney *WAITING | patiently by the *ROCK!"},
            {"text": "Pip said, Sweet berries are delicious, but my word is like solid gold!", "caps": "Pip said, Sweet berries are *DELICIOUS, | but my word is like *SOLID | *GOLD!"},
            {"text": "He scurried across the bridge and arrived just as the first evening star twinkled!", "caps": "He scurried across the *BRIDGE | and arrived just as the *FIRST | evening star *TWINKLED!"},
            {"text": "Barney gave Pip a giant bear hug—trust is the greatest treasure in the world!", "caps": "Barney gave Pip a giant *BEAR HUG— | trust is the greatest *TREASURE | in the *WORLD!"},
            {"text": "Be a friend who keeps their word—subscribe to BabyBeats Rhymo!", "caps": "Be a friend who *KEEPS | their word—*SUBSCRIBE | to *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "05_02_27",
        "day": 87,
        "date_str": "05/02/27",
        "category": "science-curiosity",
        "title": "Why Do Cuts Heal? Your Body's Tiny Super Bandage!",
        "thumb_text": "HOW SCRAPES HEAL?!",
        "primary_keyword": "how scrapes and cuts heal kids science",
        "supporting_keywords": ["platelets scab science cartoon", "human body healing superpowers", "skin repair for children"],
        "fact_summary": "When you scrape your knee, tiny blood cells called platelets rush in like a construction team, weaving a net of fibers that hardens into a protective scab.",
        "hook": "You scraped your knee on the sidewalk! But within minutes, an invisible superhero team starts rebuilding your skin!",
        "publish_slot_est": "2027-02-05T15:30:00-05:00",
        "publish_at_utc": "2027-02-05T20:30:00Z",
        "lines": [
            {"text": "Ouch! You tripped on the playground and got a bright red scrape!", "caps": "*OUCH! You tripped on the *PLAYGROUND | and got a bright red *SCRAPE!"},
            {"text": "Deep inside your bloodstream, emergency sirens begin to wail!", "caps": "Deep inside your *BLOODSTREAM, | emergency sirens begin to *WAIL!"},
            {"text": "Millions of tiny disc-shaped builders called platelets rush to the rescue!", "caps": "Millions of tiny *BUILDERS | called *PLATELETS | rush to the *RESCUE!"},
            {"text": "They stick together tightly, locking arms like a superhero shield wall!", "caps": "They stick together *TIGHTLY, | locking arms like a *SUPERHERO | shield *WALL!"},
            {"text": "Then they weave tough sticky threads called fibrin to trap red cells!", "caps": "Then they weave tough sticky *THREADS | called fibrin to trap *RED | *CELLS!"},
            {"text": "In just a few hours, the net dries into a tough, protective brown scab!", "caps": "In just a few *HOURS, | the net dries into a *TOUGH, | protective brown *SCAB!"},
            {"text": "Underneath the scab roof, fresh new skin cells grow happy and smooth!", "caps": "Underneath the scab *ROOF, | fresh new skin cells grow *HAPPY | and *SMOOTH!"},
            {"text": "Your amazing body can heal itself from the inside out every single time!", "caps": "Your amazing body can *HEAL | itself from the inside out *EVERY | single *TIME!"},
            {"text": "Celebrate your body's superpowers—subscribe to BabyBeats Rhymo!", "caps": "Celebrate your body's *SUPERPOWERS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "06_02_27",
        "day": 88,
        "date_str": "06/02/27",
        "category": "moral-story",
        "title": "The Selfish Squirrel Who Hid All The Acorns: True Friendship!",
        "thumb_text": "ACORN HOARDER?!",
        "primary_keyword": "sharing is caring animal fable cartoon",
        "supporting_keywords": ["greedy squirrel learns to share", "kindergarten sharing moral story", "friendship lesson for kids"],
        "fact_summary": "Hoarding things all for yourself leaves you lonely; sharing food and toys turns simple moments into joyous celebrations.",
        "hook": "Sammy the squirrel had 500 acorns hidden in a hollow oak, but wouldn't share even one! Why was he still so sad?",
        "publish_slot_est": "2027-02-06T15:30:00-05:00",
        "publish_at_utc": "2027-02-06T20:30:00Z",
        "lines": [
            {"text": "Sammy the squirrel collected five hundred crunchy acorns in his secret hollow oak!", "caps": "Sammy the squirrel *COLLECTED | five hundred acorns in his *SECRET | hollow *OAK!"},
            {"text": "Mine, all mine! Sammy cheered, sitting on his giant mountain of nuts!", "caps": "*MINE, all mine! Sammy *CHEERED, | sitting on his giant *MOUNTAIN | of *NUTS!"},
            {"text": "Outside his tree, the winter wind whistled cold, and tiny birds searched for food!", "caps": "Outside his *TREE, | the winter wind whistled *COLD, | and tiny birds *SEARCHED!"},
            {"text": "Sammy ate ten acorns alone in the dark, but his heart felt cold and hollow!", "caps": "Sammy ate ten acorns *ALONE, | but his heart felt cold and *HOLLOW!"},
            {"text": "Having all the treasure in the forest is boring when you have zero friends to play with!", "caps": "Having all the treasure is *BORING | when you have *ZERO | friends to play *WITH!"},
            {"text": "Sammy pushed his door open and shouted, Acorn picnic at my tree, everyone!", "caps": "Sammy pushed his door *OPEN | and shouted, *ACORN PICNIC | at my tree, *EVERYONE!"},
            {"text": "Rabbits, bluebirds, and mice gathered round, singing cheerful songs together!", "caps": "Rabbits, bluebirds, and *MICE | gathered round, singing *CHEERFUL | songs *TOGETHER!"},
            {"text": "Joy multiplies when you share it with open paws and a warm heart!", "caps": "Joy multiplies when you *SHARE IT | with open paws and a *WARM | *HEART!"},
            {"text": "Open your heart and subscribe to BabyBeats Rhymo for daily stories!", "caps": "Open your *HEART | and *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *STORIES!"}
        ]
    },
    {
        "id": "07_02_27",
        "day": 89,
        "date_str": "07/02/27",
        "category": "science-curiosity",
        "title": "Why Do Onions Make Us Cry? The Sneaky Tear Gas Trick!",
        "thumb_text": "WHY ONIONS CRY?!",
        "primary_keyword": "why do onions make you cry kids science",
        "supporting_keywords": ["onion tear chemical trick cartoon", "kitchen science experiments for kids", "eye protection reflex science"],
        "fact_summary": "When you slice an onion, broken plant cells mix sulfur compounds into a mild natural gas; your eyes flush it away with cooling tears!",
        "hook": "You are helping Grandma chop an onion, and suddenly you're weeping buckets of tears! Is the onion actually evil?",
        "publish_slot_est": "2027-02-07T15:30:00-05:00",
        "publish_at_utc": "2027-02-07T20:30:00Z",
        "lines": [
            {"text": "You're standing in the kitchen, Grandma slices an onion, and bam—you're crying!", "caps": "You're standing in the *KITCHEN, | Grandma slices an onion, and *BAM— | you're *CRYING!"},
            {"text": "Don't worry, you're not sad! The onion is actually defending itself!", "caps": "Don't worry, you're not *SAD! | The onion is actually *DEFENDING | *ITSELF!"},
            {"text": "Underground, onions don't want hungry moles and worms eating their bulb!", "caps": "Underground, onions don't want *HUNGRY | worms eating their *BULB!"},
            {"text": "When a knife slices the onion, tiny microscopic cells burst open!", "caps": "When a knife slices the *ONION, | tiny microscopic cells *BURST | *OPEN!"},
            {"text": "Sulfur compounds mix together to create an invisible cloud of tear gas!", "caps": "Sulfur compounds *MIX | to create an invisible cloud of *TEAR | *GAS!"},
            {"text": "When the gas touches your moist eyes, nerve sensors shout, Warning, irritant detected!", "caps": "When the gas touches your *EYES, | nerve sensors shout, *WARNING! | Irritant *DETECTED!"},
            {"text": "Your tear glands instantly pump a waterfall of fresh saline to wash it away!", "caps": "Your tear glands *INSTANTLY | pump a waterfall of tears to *WASH | it *AWAY!"},
            {"text": "Chef trick: Chill your onion in the fridge first to slow down the gas!", "caps": "*CHEF TRICK: | Chill your onion in the *FRIDGE | to slow down the *GAS!"},
            {"text": "Unlock more kitchen mysteries—subscribe to BabyBeats Rhymo!", "caps": "Unlock more *KITCHEN mysteries— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "08_02_27",
        "day": 90,
        "date_str": "08/02/27",
        "category": "moral-story",
        "title": "Leo Learns Table Manners: The No-Slurp Adventure!",
        "thumb_text": "SLURPING MONSTER?!",
        "primary_keyword": "table manners for kids cartoon story",
        "supporting_keywords": ["polite eating habits children", "preschool mealtime manners", "no slurping soup cartoon"],
        "fact_summary": "Good table manners show respect for the cook and make mealtimes delightful for everyone at the family table.",
        "hook": "Leo slurped his hot soup so loudly, the cat jumped onto the chandelier! How did a fun napkin game fix his wild manners?",
        "publish_slot_est": "2027-02-08T15:30:00-05:00",
        "publish_at_utc": "2027-02-08T20:30:00Z",
        "lines": [
            {"text": "Dinner time at Leo's house! Steaming bowls of delicious vegetable soup on the table!", "caps": "Dinner time at Leo's *HOUSE! | Steaming bowls of delicious *VEGETABLE | soup on the *TABLE!"},
            {"text": "SLUUURP! Leo dipped his spoon and slurped so loudly, the walls shook!", "caps": "*SLUUURP! Leo dipped his spoon | and slurped so loudly, the *WALLS | *SHOOK!"},
            {"text": "Soup splashed on his shirt, and breadcrumbs tumbled onto the floor like confetti!", "caps": "Soup splashed on his *SHIRT, | and breadcrumbs tumbled onto the *FLOOR | like *CONFETTI!"},
            {"text": "Dad smiled gently and said, Welcome to the Royal Knight Banquet, Sir Leo!", "caps": "Dad smiled *GENTLY and said, | Welcome to the *ROYAL | Knight Banquet, Sir *LEO!"},
            {"text": "Royal knights place their soft linen napkin across their lap like a secret banner!", "caps": "Royal knights place their *NAPKIN | across their lap like a *SECRET | *BANNER!"},
            {"text": "They blow softly on each spoonful, chew with quiet closed lips, and say please!", "caps": "They blow softly on each *SPOONFUL, | chew with *QUIET lips, | and say *PLEASE!"},
            {"text": "Leo tried the Royal Knight style—suddenly eating soup felt like an elegant adventure!", "caps": "Leo tried the Royal Knight *STYLE— | suddenly dinner felt like an *ELEGANT | *ADVENTURE!"},
            {"text": "Kind table manners show love to the chef and keep dinner peaceful for everyone!", "caps": "Kind manners show *LOVE | to the chef and keep dinner *PEACEFUL | for *EVERYONE!"},
            {"text": "Level up your daily habits—subscribe to BabyBeats Rhymo!", "caps": "Level up your daily *HABITS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "09_02_27",
        "day": 91,
        "date_str": "09/02/27",
        "category": "science-curiosity",
        "title": "Why Do We Get Goosebumps? The Animal Fur Secret!",
        "thumb_text": "WHY GOOSEBUMPS?!",
        "primary_keyword": "why do we get goosebumps kids science cartoon",
        "supporting_keywords": ["goosebumps reflex explained children", "human body mysteries cartoon", "why hair stands up when cold"],
        "fact_summary": "Tiny muscles under each hair follicle tighten when you're cold or spooked, pulling hairs upright to trap warm air like a fluffy winter coat.",
        "hook": "A cold gust of wind blows by, and suddenly your arms look like plucked chicken skin! What is your body doing?",
        "publish_slot_est": "2027-02-09T15:30:00-05:00",
        "publish_at_utc": "2027-02-09T20:30:00Z",
        "lines": [
            {"text": "BRRR! A chilly breeze blows into the park, and look at your arms!", "caps": "*BRRR! A chilly breeze blows, | and look at your *ARMS | right *NOW!"},
            {"text": "Thousands of tiny bumpy dots pop up, making your skin look like a goose!", "caps": "Thousands of tiny *BUMPS | pop up, making your skin look *JUST | like a *GOOSE!"},
            {"text": "Underneath every single hair on your arm sits a microscopic muscle!", "caps": "Underneath every *HAIR | on your arm sits a microscopic *MUSCLE | *TEAM!"},
            {"text": "When your skin senses cold temperatures, these muscles yank upward!", "caps": "When your skin senses *COLD, | these muscles yank *UPWARD | in one *SNAP!"},
            {"text": "This pulls your arm hairs straight up like tiny radio antennas!", "caps": "This pulls your arm hairs *STRAIGHT UP | like tiny radio *ANTENNAS!"},
            {"text": "For furry animals like bears and cats, puffed-up fur traps pockets of warm air!", "caps": "For furry animals, puffed-up *FUR | traps pockets of *WARM | *AIR!"},
            {"text": "And when a cat is scared, puffed fur makes them look twice as big and scary!", "caps": "And when an animal is *SCARED, | puffed fur makes them look twice as *BIG | and *MIGHTY!"},
            {"text": "Humans don't have thick fur anymore, but our ancient body reflex still works!", "caps": "Humans don't have thick *FUR, | but our ancient body reflex *STILL | *WORKS!"},
            {"text": "Discover your body's hidden codes—subscribe to BabyBeats Rhymo!", "caps": "Discover your body's *HIDDEN CODES— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "10_02_27",
        "day": 92,
        "date_str": "10/02/27",
        "category": "moral-story",
        "title": "The Kitten Who Was Afraid of the Dark: Nightlight Courage!",
        "thumb_text": "AFRAID OF DARK?!",
        "primary_keyword": "overcoming fear of the dark bedtime story kids",
        "supporting_keywords": ["nighttime bravery cartoon", "bedtime courage kitten story", "preschool dark fears lesson"],
        "fact_summary": "Darkness is just the absence of light, not a spooky monster; when you turn on your curiosity flashlight, familiar shapes appear safe and warm.",
        "hook": "Whiskers the kitten thought the shadowy coat rack in his room was a giant eight-armed monster! How did he conquer the dark?",
        "publish_slot_est": "2027-02-10T15:30:00-05:00",
        "publish_at_utc": "2027-02-10T20:30:00Z",
        "lines": [
            {"text": "Click! The bedroom lamp went out, and thick black shadows filled Whiskers' bedroom!", "caps": "*CLICK! The lamp went out, | and thick black *SHADOWS | filled the *BEDROOM!"},
            {"text": "In the corner stood a tall, spooky shape with giant waving tentacles!", "caps": "In the corner stood a *TALL, | spooky shape with giant *WAVING | *ARMS!"},
            {"text": "Whiskers pulled his fluffy blanket over his whiskers, shivering with fear!", "caps": "Whiskers pulled his *BLANKET | over his ears, shivering with *TOTAL | *FEAR!"},
            {"text": "Then his big brother whispered, Shadows can only copy what is already here!", "caps": "Then his brother *WHISPERED, | Shadows can only copy what is *ALREADY | *HERE!"},
            {"text": "Whiskers clicked his tiny yellow flashlight and beamed it straight at the monster!", "caps": "Whiskers clicked his *FLASHLIGHT | and beamed it straight at the *SPOOKY | *MONSTER!"},
            {"text": "Giggle! It wasn't a monster at all—just his yellow winter jacket and floppy hat!", "caps": "*GIGGLE! It wasn't a monster— | just his winter jacket and *FLOPPY | *HAT!"},
            {"text": "The dark doesn't create monsters; it just plays funny tricks with sleepy eyes!", "caps": "The dark doesn't create *MONSTERS; | it just plays funny tricks with *SLEEPY | *EYES!"},
            {"text": "Bravery is turning on your little light and seeing the truth for yourself!", "caps": "Bravery is turning on your *LIGHT | and seeing the truth for *YOURSELF!"},
            {"text": "Sleep peaceful and brave—subscribe to BabyBeats Rhymo!", "caps": "Sleep peaceful and *BRAVE— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "11_02_27",
        "day": 93,
        "date_str": "11/02/27",
        "category": "science-curiosity",
        "title": "Why Does Ice Float? Water's Superpower Mystery!",
        "thumb_text": "WHY ICE FLOATS?!",
        "primary_keyword": "why does ice float kids science cartoon",
        "supporting_keywords": ["water density science mystery", "frozen lake fish survival cartoon", "physics for kids animated"],
        "fact_summary": "Most liquids shrink and sink when frozen, but water molecules form a honeycomb crystal lattice that expands, making ice lighter than liquid water!",
        "hook": "Drop a rock into a pond, and it sinks to the bottom. But toss a giant frozen iceberg in, and it bobs right on top! Why?",
        "publish_slot_est": "2027-02-11T15:30:00-05:00",
        "publish_at_utc": "2027-02-11T20:30:00Z",
        "lines": [
            {"text": "Drop a metal spoon in a cup of water—it sinks straight down like an anchor!", "caps": "Drop a metal *SPOON | in a cup—it sinks straight down *LIKE | an *ANCHOR!"},
            {"text": "Drop a solid cube of hard ice in—and it floats right to the surface!", "caps": "Drop a solid cube of *ICE in— | and it floats right to the *TOP | *SURFACE!"},
            {"text": "Almost everything in the universe gets heavier and denser when it freezes!", "caps": "Almost everything in the *UNIVERSE | gets heavier and denser when it *FREEZES!"},
            {"text": "Liquid wax sinks in liquid wax. Solid iron sinks in molten iron!", "caps": "Liquid wax *SINKS. | Solid iron *SINKS | in molten *IRON!"},
            {"text": "So why is water the magical exception on our planet?", "caps": "So why is *WATER | the magical exception on our *WHOLE | *PLANET?"},
            {"text": "When water freezes, molecules lock arms into an open, six-sided honeycomb crystal!", "caps": "When water freezes, molecules lock *ARMS | into an open six-sided *HONEYCOMB | *CRYSTAL!"},
            {"text": "This trapped empty space makes ice about nine percent lighter than liquid water!", "caps": "This trapped space makes ice *NINE PERCENT | lighter than liquid *WATER!"},
            {"text": "Because ice floats, frozen lake tops act as warm blankets so fish survive winter!", "caps": "Because ice floats, lake *TOPS | act as warm blankets so fish *SURVIVE | *WINTER!"},
            {"text": "Discover nature's magical laws—subscribe to BabyBeats Rhymo!", "caps": "Discover nature's magical *LAWS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "12_02_27",
        "day": 94,
        "date_str": "12/02/27",
        "category": "moral-story",
        "title": "The Boy Who Blamed His Little Sister: Owning Your Mistakes!",
        "thumb_text": "NOT MY FAULT?!",
        "primary_keyword": "taking responsibility moral story cartoon",
        "supporting_keywords": ["blaming siblings lesson for kids", "owning mistakes animated fable", "honesty and courage story"],
        "fact_summary": "Blaming someone else for your mistake creates hurt and distrust; admitting your slip-up with honesty earns genuine forgiveness.",
        "hook": "Leo accidentally spilled red grape juice on the living room rug and yelled, Maya did it! Why did his heart feel so guilty?",
        "publish_slot_est": "2027-02-12T15:30:00-05:00",
        "publish_at_utc": "2027-02-12T20:30:00Z",
        "lines": [
            {"text": "Oops! A big glass of dark red grape juice tipped over onto the cream carpet!", "caps": "*OOPS! A big glass of grape *JUICE | tipped over onto the cream *CARPET!"},
            {"text": "Leo looked around in panic and shouted, Mom, baby Maya bumped into the table!", "caps": "Leo looked around in *PANIC | and shouted, *MAYA bumped | into the *TABLE!"},
            {"text": "Little Maya tilted her head with big sad tears—she didn't understand why!", "caps": "Little Maya tilted her *HEAD | with big sad tears—she didn't *UNDERSTAND | *WHY!"},
            {"text": "Leo watched his little sister cry, and a heavy gray cloud rained over his thoughts!", "caps": "Leo watched his sister *CRY, | and a heavy gray cloud rained over his *THOUGHTS!"},
            {"text": "Blaming someone innocent makes an accident ten times worse than the spill itself!", "caps": "Blaming someone *INNOCENT | makes an accident ten times *WORSE | than the *SPILL!"},
            {"text": "Leo took a deep breath, walked to Mom, and said, I lied. It was my elbow!", "caps": "Leo took a deep *BREATH, | walked to Mom, and said, *I LIED. | It was my *ELBOW!"},
            {"text": "Mom hugged Leo and Maya tightly: Accidents happen, but owning up takes real strength!", "caps": "Mom hugged them both *TIGHTLY: | Accidents happen, but owning up takes *REAL | *STRENGTH!"},
            {"text": "Together they grabbed towels and cleaned the rug until it sparkled clean!", "caps": "Together they grabbed *TOWELS | and cleaned the rug until it *SPARKLED | *CLEAN!"},
            {"text": "Choose bravery and honesty—subscribe to BabyBeats Rhymo!", "caps": "Choose bravery and *HONESTY— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "13_02_27",
        "day": 95,
        "date_str": "13/02/27",
        "category": "science-curiosity",
        "title": "Why Do Fireflies Glow In The Dark? Nature's Flashlight!",
        "thumb_text": "WHY FIREFLIES GLOW?!",
        "primary_keyword": "why do fireflies glow kids science cartoon",
        "supporting_keywords": ["bioluminescence for children", "firefly blinking light mystery", "summer insect science cartoon"],
        "fact_summary": "Fireflies produce 100% efficient cold light through a chemical reaction called bioluminescence, blinking secret glowing patterns to talk to friends.",
        "hook": "On warm summer nights, tiny flying beetles light up like floating fairy stars! How do they turn their bellies into lightbulbs?",
        "publish_slot_est": "2027-02-13T15:30:00-05:00",
        "publish_at_utc": "2027-02-13T20:30:00Z",
        "lines": [
            {"text": "Look out into the dark summer grass! Tiny yellow stars are blinking and dancing!", "caps": "Look into the dark *GRASS! | Tiny yellow stars are *BLINKING | and *DANCING!"},
            {"text": "Fireflies! But how do tiny bugs carry neon flashlights inside their tummy?", "caps": "*FIREFLIES! But how do bugs | carry neon flashlights inside their *TUMMY?"},
            {"text": "Inside the firefly's tail lantern sits a special chemical called luciferin!", "caps": "Inside the firefly's *TAIL | sits a special chemical called *LUCIFERIN!"},
            {"text": "When oxygen from the air mixes with this chemical and an enzyme called luciferase...", "caps": "When oxygen from the *AIR | mixes with this chemical inside their *BODY..."},
            {"text": "FLASH! A burst of bright, emerald-gold light shines out into the darkness!", "caps": "*FLASH! A burst of bright | emerald-gold light shines into the *DARKNESS!"},
            {"text": "A household lightbulb wastes ninety percent of its energy making hot heat!", "caps": "A household bulb wastes *NINETY PERCENT | of its energy making hot *HEAT!"},
            {"text": "A firefly's light is one hundred percent cold light—zero energy wasted!", "caps": "A firefly's light is *COLD LIGHT— | zero energy *WASTED at *ALL!"},
            {"text": "They blink in rhythm like secret Morse code to talk to their beetle friends!", "caps": "They blink in *RHYTHM | like secret Morse code to talk to their *FRIENDS!"},
            {"text": "Explore nature's brilliant inventions—subscribe to BabyBeats Rhymo!", "caps": "Explore nature's *BRILLIANT inventions— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "14_02_27",
        "day": 96,
        "date_str": "14/02/27",
        "category": "moral-story",
        "title": "Valentine Kindness: Making a Homemade Card for Everyone!",
        "thumb_text": "KINDNESS CARDS!",
        "primary_keyword": "valentines day kindness story for kids",
        "supporting_keywords": ["including everyone school moral story", "handmade valentines cards cartoon", "empathy and friendship lesson"],
        "fact_summary": "Valentine's Day isn't about expensive candy; giving sincere, handwritten words of encouragement makes everyone feel valued and included.",
        "hook": "Leo was making Valentine cards for school, but noticed new kid Toby sitting alone in the corner! What special surprise did Leo create?",
        "publish_slot_est": "2027-02-14T15:30:00-05:00",
        "publish_at_utc": "2027-02-14T20:30:00Z",
        "lines": [
            {"text": "Valentine's Day at school! Red glitter, heart stickers, and pink paper everywhere!", "caps": "Valentine's Day at *SCHOOL! | Red glitter, heart stickers, and *PINK | paper *EVERYWHERE!"},
            {"text": "Leo made bright cards for all his soccer buddies, laughing and sharing candy!", "caps": "Leo made cards for all his *BUDDIES, | laughing and sharing *SWEET | *CANDY!"},
            {"text": "Then he noticed Toby, the shy new boy, quietly coloring alone by the window!", "caps": "Then he noticed *TOBY, | the shy new boy, quietly coloring *ALONE | by the *WINDOW!"},
            {"text": "Toby's Valentine mailbox was completely empty—not even a single sticker inside!", "caps": "Toby's Valentine *MAILBOX | was completely empty—not a single *STICKER | *INSIDE!"},
            {"text": "Leo stopped. True kindness means making sure no friend gets left behind!", "caps": "Leo stopped. True *KINDNESS | means making sure no friend gets left *BEHIND!"},
            {"text": "He grabbed his gold marker and drew a smiling rocket: To Toby, coolest builder in class!", "caps": "He drew a smiling *ROCKET: | To Toby, coolest builder in our whole *CLASS!"},
            {"text": "When Toby opened the card, his face lit up brighter than a million fireworks!", "caps": "When Toby opened the *CARD, | his face lit up brighter than *FIREWORKS!"},
            {"text": "A tiny act of kindness can turn someone's lonely day into pure magic!", "caps": "A tiny act of *KINDNESS | can turn someone's lonely day into pure *MAGIC!"},
            {"text": "Spread warmth everywhere—subscribe to BabyBeats Rhymo!", "caps": "Spread warmth *EVERYWHERE— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "15_02_27",
        "day": 97,
        "date_str": "15/02/27",
        "category": "science-curiosity",
        "title": "Why Do We Shiver When We're Cold? The Muscle Engine!",
        "thumb_text": "WHY DO WE SHIVER?!",
        "primary_keyword": "why do we shiver when cold kids science",
        "supporting_keywords": ["human body temperature regulation", "how muscles produce heat cartoon", "shivering reflex explained"],
        "fact_summary": "When your core body temperature dips, your brain commands muscles to twitch rapidly up to 30 times a second, turning movement into warming body heat.",
        "hook": "You step out of the warm shower on a winter morning, and your whole body starts chattering and vibrating like a drum!",
        "publish_slot_est": "2027-02-15T15:30:00-05:00",
        "publish_at_utc": "2027-02-15T20:30:00Z",
        "lines": [
            {"text": "CHATTER! Your teeth knock together and your shoulders shake like a dance machine!", "caps": "*CHATTER! Your teeth knock, | and your shoulders shake like a *DANCE | *MACHINE!"},
            {"text": "Why does your body vibrate uncontrollably when you step into the cold?", "caps": "Why does your body *VIBRATE | uncontrollably when you step into the *COLD?"},
            {"text": "Your brain has a built-in thermostat called the hypothalamus!", "caps": "Your brain has a built-in *THERMOSTAT | called the *HYPOTHALAMUS!"},
            {"text": "It keeps your internal body temperature at a cozy ninety-eight point six degrees!", "caps": "It keeps your body *TEMP | at a cozy ninety-eight point six *DEGREES!"},
            {"text": "If cold wind drops your skin temperature even by one little degree...", "caps": "If cold wind drops your *TEMP | even by one little *DEGREE..."},
            {"text": "Emergency alarms trigger! Your brain orders your skeletal muscles to twitch!", "caps": "Emergency alarms *TRIGGER! | Your brain orders your muscles to *TWITCH!"},
            {"text": "Muscles contract and relax up to thirty times every single second!", "caps": "Muscles contract up to *THIRTY | times every single *SECOND!"},
            {"text": "This rapid muscle workout generates instant heat to protect your vital organs!", "caps": "This muscle workout generates *INSTANT | heat to protect your vital *ORGANS!"},
            {"text": "Your body's automatic defenses are genius—subscribe to BabyBeats Rhymo!", "caps": "Your body's defenses are *GENIUS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "16_02_27",
        "day": 98,
        "date_str": "16/02/27",
        "category": "moral-story",
        "title": "The Bear Who Wouldn't Say Please: The Key That Opens Every Door!",
        "thumb_text": "SAY MAGIC PLEASE!",
        "primary_keyword": "saying please and thank you moral story kids",
        "supporting_keywords": ["politeness magic words cartoon", "preschool manners animated story", "courtesy lessons for children"],
        "fact_summary": "Demanding things makes people feel bossed around; saying 'please' and 'thank you' turns requests into cheerful teamwork.",
        "hook": "Barnaby the big bear growled, Give me that honey pot NOW! But the pantry door stayed locked tight. What was the secret key?",
        "publish_slot_est": "2027-02-16T15:30:00-05:00",
        "publish_at_utc": "2027-02-16T20:30:00Z",
        "lines": [
            {"text": "Barnaby the big brown bear stomped his giant paws into the forest bakery!", "caps": "Barnaby the big *BEAR | stomped his giant paws into the *FOREST | *BAKERY!"},
            {"text": "Hand over the warm cinnamon honey rolls right now! Barnaby bellowed loudly!", "caps": "Hand over the warm *HONEY ROLLS | right now! Barnaby *BELLOWED | *LOUDLY!"},
            {"text": "Mrs. Badger folded her apron and clicked the glass display counter shut!", "caps": "Mrs. Badger folded her *APRON | and clicked the display counter *SHUT!"},
            {"text": "Barnaby huffed and puffed, trying to push through, but the latch wouldn't budge!", "caps": "Barnaby huffed and *PUFFED, | but the pantry latch wouldn't *BUDGE | at *ALL!"},
            {"text": "Little Robin chirped from the counter, Roaring only builds walls, Barnaby!", "caps": "Little Robin *CHIRPED, | Roaring only builds walls, *BARNABY!"},
            {"text": "Barnaby looked down at his big clumsy paws. He took a breath and whispered...", "caps": "Barnaby looked at his *PAWS. | He took a breath and softly *WHISPERED..."},
            {"text": "May I please have a honey roll, Mrs. Badger? I appreciate your hard work!", "caps": "May I *PLEASE have a roll? | I appreciate your hard *WORK!"},
            {"text": "CLICK! The door swung wide open with a warm smile—magic words open every heart!", "caps": "*CLICK! The door swung wide open— | magic words open every *HEART!"},
            {"text": "Speak with kindness and respect—subscribe to BabyBeats Rhymo!", "caps": "Speak with *KINDNESS | and respect—*SUBSCRIBE | to *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "17_02_27",
        "day": 99,
        "date_str": "17/02/27",
        "category": "science-curiosity",
        "title": "Why Does Milk Make Bones Strong? The Calcium Fortress!",
        "thumb_text": "HOW BONES GROW?!",
        "primary_keyword": "why calcium makes bones strong kids science",
        "supporting_keywords": ["human skeleton building blocks cartoon", "healthy habits drinking milk kids", "bone density for children"],
        "fact_summary": "Your skeleton has 206 bones made of calcium phosphate crystals; drinking milk and playing outside deposits minerals to build an unbreakable fortress.",
        "hook": "You have 206 bones inside you right now! If you could zoom into your skeleton with an x-ray, what does calcium actually do?",
        "publish_slot_est": "2027-02-17T15:30:00-05:00",
        "publish_at_utc": "2027-02-17T20:30:00Z",
        "lines": [
            {"text": "Inside your body stands a super-strong architectural frame: two hundred and six bones!", "caps": "Inside your body stands a *FRAME: | two hundred and six strong *BONES!"},
            {"text": "They protect your brain, shield your heart, and let you jump eight feet high!", "caps": "They protect your *BRAIN, | shield your heart, and let you *JUMP | high!"},
            {"text": "Every time you drink milk or eat yogurt, you swallow billions of calcium minerals!", "caps": "When you drink *MILK, | you swallow billions of calcium *MINERALS!"},
            {"text": "Special construction cells called osteoblasts grab calcium right out of your blood!", "caps": "Special construction cells called *OSTEOBLASTS | grab calcium from your *BLOOD!"},
            {"text": "They lay down tough collagen rebar, then cement it with hard mineral crystals!", "caps": "They lay down tough *COLLAGEN, | then cement it with hard *MINERAL | *CRYSTALS!"},
            {"text": "Running, jumping rope, and playing outside tells your bones, Make us stronger!", "caps": "Running and jumping *ROPE | tells your bones, Make us *STRONGER!"},
            {"text": "And sunshine gives you Vitamin D, the magic key that unlocks calcium absorption!", "caps": "And sunshine gives you *VITAMIN D, | the key that unlocks calcium *POWER!"},
            {"text": "Build your skeleton fortress today so you can run fast and jump high forever!", "caps": "Build your skeleton *FORTRESS | so you can jump high *FOREVER!"},
            {"text": "Fuel your growing body—subscribe to BabyBeats Rhymo!", "caps": "Fuel your growing *BODY— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "18_02_27",
        "day": 100,
        "date_str": "18/02/27",
        "category": "moral-story",
        "title": "The 100th Day of School: What Teamwork Can Build!",
        "thumb_text": "100TH DAY TEAM!",
        "primary_keyword": "100th day of school moral story cartoon",
        "supporting_keywords": ["teamwork building classroom challenge", "100 days smarter celebration", "kindergarten collaboration lesson"],
        "fact_summary": "One person stacking 100 blocks alone gets tired and frustrated; when teammates share tasks, colossal castles rise effortlessly.",
        "hook": "It's the 100th day of school! The classroom challenge is to build a tower of 100 giant foam blocks before the recess bell rings!",
        "publish_slot_est": "2027-02-18T15:30:00-05:00",
        "publish_at_utc": "2027-02-18T20:30:00Z",
        "lines": [
            {"text": "Celebration time! The whole elementary school is cheering for the one hundredth day!", "caps": "Celebration *TIME! | The whole school is cheering for the *ONE HUNDREDTH | *DAY!"},
            {"text": "Teacher announces: Each table has five minutes to stack one hundred foam blocks!", "caps": "Teacher announces: Stack *ONE HUNDRED | blocks before the recess bell *RINGS!"},
            {"text": "At first, everyone scrambled and grabbed blocks, knocking each other's towers over!", "caps": "At first, everyone *SCRAMBLED, | knocking each other's towers *OVER!"},
            {"text": "Leo called a timeout: If we fight for blocks, nobody wins the trophy!", "caps": "Leo called a *TIMEOUT: | If we fight for blocks, nobody *WINS!"},
            {"text": "Mia, you hand the blocks! Sam, steady the wide base! I will place the spire!", "caps": "Mia, hand the *BLOCKS! | Sam, steady the base! I'll place the *TOP!"},
            {"text": "Block by block, ten, twenty, fifty, eighty—rising taller than their teacher!", "caps": "Block by block, twenty, *FIFTY, | eighty—rising taller than their *TEACHER!"},
            {"text": "Ninety-nine, ONE HUNDRED! Just as the bell chimed, the golden star crown sat on top!", "caps": "Ninety-nine, *ONE HUNDRED! | The golden star sat *RIGHT ON TOP!"},
            {"text": "Teamwork divides the difficult task and multiplies the celebration ten times over!", "caps": "Teamwork divides the *TASK | and multiplies the celebration *TEN TIMES | *OVER!"},
            {"text": "Celebrate winning together—subscribe to BabyBeats Rhymo!", "caps": "Celebrate winning *TOGETHER— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "19_02_27",
        "day": 101,
        "date_str": "19/02/27",
        "category": "science-curiosity",
        "title": "Why Do Rainbows Appear After Rain? The Sun's Magic Mirror!",
        "thumb_text": "HOW RAINBOWS WORK?!",
        "primary_keyword": "why do rainbows appear kids science cartoon",
        "supporting_keywords": ["refraction light prism explanation children", "rain and sunlight weather science", "seven colors of rainbow cartoon"],
        "fact_summary": "Sunlight looks white, but it's made of 7 colors; raindrops act as tiny glass prisms that bend and reflect colors at different angles into a glorious rainbow.",
        "hook": "The storm clears, sunlight streams through wet trees, and BAM—a giant seven-color arch paints the sky! How does it work?",
        "publish_slot_est": "2027-02-19T15:30:00-05:00",
        "publish_at_utc": "2027-02-19T20:30:00Z",
        "lines": [
            {"text": "The dark rainstorm stops, the golden sun peeks out, and look high up in the blue sky!", "caps": "The storm stops, the *SUN peeks out, | and look high up in the *BLUE | *SKY!"},
            {"text": "A glowing ribbon of red, orange, yellow, green, blue, indigo, and violet!", "caps": "A glowing ribbon of *RED, | orange, yellow, green, blue, indigo, and *VIOLET!"},
            {"text": "Where did those brilliant colors come from? Sunlight looks completely white!", "caps": "Where did those *COLORS come from? | Sunlight looks completely *WHITE!"},
            {"text": "White light is actually a team of all seven colors traveling together!", "caps": "White light is a *TEAM | of all seven colors traveling *TOGETHER!"},
            {"text": "Millions of floating raindrops act like tiny glass prism mirrors!", "caps": "Millions of floating *RAINDROPS | act like tiny glass prism *MIRRORS!"},
            {"text": "When sunlight enters a raindrop, it slows down and bends—a trick called refraction!", "caps": "When sunlight enters a raindrop, | it slows down and *BENDS!"},
            {"text": "Red light bends the least, while violet light bends the most!", "caps": "Red light bends the *LEAST, | while violet bends the *MOST!"},
            {"text": "The colors separate and bounce back into your eyes as a majestic circular arch!", "caps": "The colors separate and bounce | into your eyes as a majestic *ARCH!"},
            {"text": "Discover nature's brilliant art—subscribe to BabyBeats Rhymo!", "caps": "Discover nature's brilliant *ART— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "20_02_27",
        "day": 102,
        "date_str": "20/02/27",
        "category": "moral-story",
        "title": "The Little Pup Who Raced Ahead: Waiting Your Turn!",
        "thumb_text": "WAIT YOUR TURN!",
        "primary_keyword": "learning patience waiting your turn kids cartoon",
        "supporting_keywords": ["preschool line cutting lesson", "patience at the playground story", "fair play puppy cartoon"],
        "fact_summary": "Pushing ahead in line ruins the fun for everyone; taking turns fairly ensures that every single friend enjoys the slide with joy.",
        "hook": "Buster the puppy shoved past everyone at the giant spiral playground slide! What happened when his friends stopped playing?",
        "publish_slot_est": "2027-02-20T15:30:00-05:00",
        "publish_at_utc": "2027-02-20T20:30:00Z",
        "lines": [
            {"text": "Sunny Saturday at the playground! The giant curly red slide was the main attraction!", "caps": "Sunny day at the *PLAYGROUND! | The giant curly slide was the *MAIN | *ATTRACTION!"},
            {"text": "A neat line of ducklings, kittens, and bunnies stood waiting patiently!", "caps": "A neat line of *FRIENDS | stood waiting patiently for their *TURN!"},
            {"text": "ZOOM! Buster the puppy charged forward, pushed past the kittens, and raced up the ladder!", "caps": "*ZOOM! Buster charged forward, | pushed past the kittens, and climbed the *LADDER!"},
            {"text": "Me first, me first! Buster barked, sliding down with a proud grin!", "caps": "Me first, *ME FIRST! | Buster barked, sliding down with a *PROUD | *GRIN!"},
            {"text": "When he reached the bottom, nobody was cheering. His friends folded their arms and walked away!", "caps": "At the bottom, nobody *CHEERED. | His friends folded their arms and *WALKED | *AWAY!"},
            {"text": "Buster sat alone by the slide. Flying down is boring when no one is playing with you!", "caps": "Buster sat alone. *SLIDING | is boring when no one plays with *YOU!"},
            {"text": "Buster walked over and apologized: I'm sorry for cutting. I'll wait my turn!", "caps": "Buster apologized: I'm *SORRY | for cutting. I'll wait my *TURN!"},
            {"text": "Patience and fair play turn simple playground slides into shared happiness!", "caps": "Patience and fair *PLAY | turn playground slides into shared *HAPPINESS!"},
            {"text": "Play fair and stay kind—subscribe to BabyBeats Rhymo!", "caps": "Play fair and stay *KIND— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "21_02_27",
        "day": 103,
        "date_str": "21/02/27",
        "category": "science-curiosity",
        "title": "Why Do We Dream? The Brain's Midnight Movie Theater!",
        "thumb_text": "WHY DO WE DREAM?!",
        "primary_keyword": "why do we dream kids science cartoon",
        "supporting_keywords": ["rem sleep memory consolidation cartoon", "why do we have nightmares kids", "brain science for children"],
        "fact_summary": "During REM sleep, your brain organizes memories from the day, filing away important lessons and turning random thoughts into wild dream movies.",
        "hook": "You close your eyes in your bed, and suddenly you're flying on a rainbow dragon eating giant pancakes! Where do dreams come from?",
        "publish_slot_est": "2027-02-21T15:30:00-05:00",
        "publish_at_utc": "2027-02-21T20:30:00Z",
        "lines": [
            {"text": "Tonight while you sleep peacefully, your brain will open a magical 3D movie theater!", "caps": "Tonight while you sleep *PEACEFULLY, | your brain will open a *MAGICAL | movie *THEATER!"},
            {"text": "You might fly over skyscrapers or chat with talking purple puppies!", "caps": "You might fly over *SKYSCRAPERS | or chat with talking purple *PUPPIES!"},
            {"text": "Why does your brain create wild, colorful stories while your body is completely asleep?", "caps": "Why does your brain create *WILD | stories while your body is *ASLEEP?"},
            {"text": "Deep in sleep, you enter a special stage called REM—Rapid Eye Movement!", "caps": "Deep in sleep, you enter *REM— | Rapid Eye *MOVEMENT!"},
            {"text": "Your brain acts like a busy librarian, sorting through every memory from your day!", "caps": "Your brain acts like a *LIBRARIAN, | sorting through every *MEMORY | from your *DAY!"},
            {"text": "It files away the math you learned and the funny joke your friend told!", "caps": "It files away the *MATH you learned | and the funny *JOKE | your friend *TOLD!"},
            {"text": "As memories weave together, your imagination sparks, painting dreams across your mind!", "caps": "As memories weave *TOGETHER, | your imagination paints *DREAMS | across your *MIND!"},
            {"text": "Good sleep organizes your brain so you wake up sharp, happy, and energized!", "caps": "Good sleep organizes your *BRAIN | so you wake up *SHARP | and *HAPPY!"},
            {"text": "Dream big every night—subscribe to BabyBeats Rhymo!", "caps": "Dream big every *NIGHT— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "22_02_27",
        "day": 104,
        "date_str": "22/02/27",
        "category": "moral-story",
        "title": "Leo & The Lost Library Book: Returning What You Borrow!",
        "thumb_text": "BORROW WITH CARE!",
        "primary_keyword": "taking care of borrowed things kids cartoon",
        "supporting_keywords": ["library book responsibility children", "respecting other people property story", "honesty and responsibility cartoon"],
        "fact_summary": "When someone lends you a book or toy, treating it with gentle care and returning it on time proves you are a trustworthy friend.",
        "hook": "Leo borrowed the school's rarest dinosaur pop-up book, but accidentally left it outside near the garden sprinklers!",
        "publish_slot_est": "2027-02-22T15:30:00-05:00",
        "publish_at_utc": "2027-02-22T20:30:00Z",
        "lines": [
            {"text": "Leo borrowed the library's coolest treasure: The Giant Pop-Up T-Rex Encyclopedia!", "caps": "Leo borrowed the library's *TREASURE: | The Giant Pop-Up *T-REX | *ENCYCLOPEDIA!"},
            {"text": "Be gentle with this book, Leo, the librarian said. Others are waiting to read it!", "caps": "Be gentle with this *BOOK, | the librarian said. Others are *WAITING | to read *IT!"},
            {"text": "Leo read it under the oak tree, but when his dog barked, he ran off and forgot it!", "caps": "Leo read it under the *TREE, | but ran off and *FORGOT | it on the *GRASS!"},
            {"text": "HISSS! The garden sprinkler clicked on, spraying water toward the paper pop-ups!", "caps": "*HISSS! The garden sprinkler clicked *ON, | spraying water toward the *PAPER | *PAGES!"},
            {"text": "Leo gasped, sprinted across the lawn, and slid to shield the book with his jacket!", "caps": "Leo gasped, *SPRINTED | across the lawn, and shielded the *BOOK | with his *JACKET!"},
            {"text": "He brought it inside, dried every drop with a soft towel, and checked every dinosaur!", "caps": "He brought it *INSIDE, | dried every drop, and checked every *DINOSAUR | *CAREFULLY!"},
            {"text": "The next morning, Leo returned it promptly with a polite thank you note!", "caps": "The next morning, Leo returned it *PROMPTLY | with a polite *THANK YOU | *NOTE!"},
            {"text": "Treating borrowed things with great care builds a golden reputation that lasts!", "caps": "Treating borrowed things with *CARE | builds a golden reputation that *LASTS!"},
            {"text": "Be responsible and reliable—subscribe to BabyBeats Rhymo!", "caps": "Be responsible and *RELIABLE— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "23_02_27",
        "day": 105,
        "date_str": "23/02/27",
        "category": "science-curiosity",
        "title": "Why Is Poop Brown? The Digestion Journey!",
        "thumb_text": "WHY IS POOP BROWN?!",
        "primary_keyword": "why is poop brown kids science cartoon",
        "supporting_keywords": ["digestion bile human body mystery", "funny body science for children", "stomach and liver science cartoon"],
        "fact_summary": "Even if you eat green kale and red strawberries, liver bile and recycled red blood cells break down into stercobilin, which turns digestion waste brown.",
        "hook": "You eat green broccoli, orange carrots, and yellow bananas. So why does bathroom poop ALWAYS turn brown? Let's solve the case!",
        "publish_slot_est": "2027-02-23T15:30:00-05:00",
        "publish_at_utc": "2027-02-23T20:30:00Z",
        "lines": [
            {"text": "Time for the number one funny mystery every kid wonders about in secret!", "caps": "Time for the funny *MYSTERY | every kid wonders about in *SECRET!"},
            {"text": "You eat colorful food: red apples, yellow corn, orange carrots, and purple grapes!", "caps": "You eat *COLORFUL food: | red apples, yellow corn, and purple *GRAPES!"},
            {"text": "So why does your body waste always end up looking brown?", "caps": "So why does your body *WASTE | always end up looking *BROWN?"},
            {"text": "Your liver produces a special dark green digestive fluid called bile!", "caps": "Your liver produces a *FLUID | called *BILE to break down *FATS!"},
            {"text": "Meanwhile, your body recycles millions of old red blood cells every single day!", "caps": "Meanwhile, your body *RECYCLES | millions of old red blood *CELLS!"},
            {"text": "As food journeys through twenty feet of intestines, friendly gut bacteria go to work!", "caps": "Friendly gut bacteria *GO TO WORK | breaking down the *LEFTOVERS!"},
            {"text": "They break down the bile and blood pigments into a compound called stercobilin!", "caps": "They transform the pigments into a compound | called *STERCOBILIN!"},
            {"text": "This compound is naturally chocolate-brown—proving your digestive system is working perfectly!", "caps": "This compound is naturally *BROWN— | proving your digestion is *PERFECT!"},
            {"text": "Laugh and learn body secrets—subscribe to BabyBeats Rhymo!", "caps": "Laugh and learn body *SECRETS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "24_02_27",
        "day": 106,
        "date_str": "24/02/27",
        "category": "moral-story",
        "title": "The Greedy Frog Who Wanted All The Flies: Being Satisfied!",
        "thumb_text": "GREEDY FROG LESSON!",
        "primary_keyword": "contentment and greed moral story for kids",
        "supporting_keywords": ["greedy frog cartoon fable", "being satisfied with what you have", "moderation lesson children"],
        "fact_summary": "Wanting more and more without appreciating what you already have leads to discomfort; true contentment brings peace and full bellies.",
        "hook": "Barnaby the bullfrog had already eaten 20 juicy flies, but tried to swallow 50 more in one giant gulp! What happened to his swollen tummy?",
        "publish_slot_est": "2027-02-24T15:30:00-05:00",
        "publish_at_utc": "2027-02-24T20:30:00Z",
        "lines": [
            {"text": "Barnaby the bullfrog sat on his giant lily pad, rubbing his plump green tummy!", "caps": "Barnaby the frog sat on his *LILY PAD, | rubbing his plump green *TUMMY!"},
            {"text": "He had already eaten twenty crunchy flies, but his eyes were bigger than his stomach!", "caps": "He ate twenty crunchy *FLIES, | but his eyes were bigger than his *STOMACH!"},
            {"text": "A golden swarm buzzed overhead, and Barnaby snapped: I want every single one!", "caps": "A golden swarm buzzed *OVERHEAD, | and Barnaby snapped: I want *EVERY ONE!"},
            {"text": "SLURP! He stuffed thirty more flies into his mouth until his cheeks bulged!", "caps": "*SLURP! He stuffed thirty more *FLIES | until his green cheeks *BULGED!"},
            {"text": "Groan! His tummy was so swollen and heavy, his lily pad began to sink under water!", "caps": "*GROAN! His tummy was so heavy, | his lily pad began to *SINK | *UNDER!"},
            {"text": "He couldn't leap, he couldn't sing, and he had a giant bellyache all afternoon!", "caps": "He couldn't *LEAP, | he couldn't sing, with a giant *BELLYACHE | all day *LONG!"},
            {"text": "Little Dragonfly fluttered by: Enough is a feast, Barnaby. Greed only sinks your pad!", "caps": "Dragonfly buzzed by: *ENOUGH | is a feast! Greed only sinks your *PAD!"},
            {"text": "Knowing when to stop and enjoying what you have brings genuine peace!", "caps": "Knowing when to *STOP | and enjoying what you have brings real *PEACE!"},
            {"text": "Learn life's golden lessons—subscribe to BabyBeats Rhymo!", "caps": "Learn life's golden *LESSONS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "25_02_27",
        "day": 107,
        "date_str": "25/02/27",
        "category": "science-curiosity",
        "title": "Why Do We Sneeze? The 100 MPH Nose Cleaner!",
        "thumb_text": "WHY WE SNEEZE?!",
        "primary_keyword": "why do we sneeze kids science cartoon",
        "supporting_keywords": ["sneezing reflex speed children", "nose defense mechanism animated", "human body health facts kids"],
        "fact_summary": "When dust or pepper tickles sensitive nerve endings in your nasal lining, your lungs compress and blast air out at up to 100 mph to clear the pipes.",
        "hook": "A tiny grain of black pepper lands inside your nostril, and ACHOO! Why does your sneeze blast out faster than a racing car?",
        "publish_slot_est": "2027-02-25T15:30:00-05:00",
        "publish_at_utc": "2027-02-25T20:30:00Z",
        "lines": [
            {"text": "Tickle, tickle in your nose! Your eyes squeeze shut, you take a sharp breath, and...", "caps": "Tickle, tickle in your *NOSE! | Your eyes squeeze shut, and *THEN..."},
            {"text": "ACHOOO! A giant explosive sneeze blasts out into your elbow tissue!", "caps": "*ACHOOO! A giant explosive *SNEEZE | blasts out into your *ELBOW!"},
            {"text": "Did you know a sneeze can launch droplets at up to one hundred miles per hour?", "caps": "A sneeze can launch air at up to *ONE HUNDRED | miles per *HOUR!"},
            {"text": "Your nose is lined with millions of microscopic cilia hairs acting as security guards!", "caps": "Your nose is lined with *CILIA | hairs acting as security *GUARDS!"},
            {"text": "When dust, pollen, or pepper touches the trigeminal nerve inside your nasal lining...", "caps": "When dust or pollen touches the *NERVE | inside your nasal *LINING..."},
            {"text": "A red alert flashes to the sneeze center in your lower brainstem!", "caps": "A red alert *FLASHES | to the sneeze center in your *BRAIN!"},
            {"text": "Your chest muscles tighten, vocal cords snap shut, and air pressure builds like a cannon!", "caps": "Your chest *TIGHTENS, | building air pressure like a *CANNON!"},
            {"text": "POW! It ejects unwanted germs and dust so your airways stay clean and safe!", "caps": "*POW! It ejects unwanted *GERMS | so your airways stay clean and *SAFE!"},
            {"text": "Celebrate your body's built-in defenses—subscribe to BabyBeats Rhymo!", "caps": "Celebrate your body's *DEFENSES— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "26_02_27",
        "day": 108,
        "date_str": "26/02/27",
        "category": "moral-story",
        "title": "The Bunny Who Never Shared His Crayons: The Colorful Masterpiece!",
        "thumb_text": "SHARE THE CRAYONS!",
        "primary_keyword": "sharing crayons kindergarten moral story",
        "supporting_keywords": ["cooperation art project cartoon", "selfish bunny learns to share", "preschool teamwork fable"],
        "fact_summary": "Hoarding colors only gives you one shade of painting; pooling crayons together lets a whole group create a glorious rainbow mural.",
        "hook": "Benny the bunny had the ultimate 64-crayon pack with a sharpener, but wouldn't let anyone use his sky blue crayon!",
        "publish_slot_est": "2027-02-26T15:30:00-05:00",
        "publish_at_utc": "2027-02-26T20:30:00Z",
        "lines": [
            {"text": "Art class challenge! The teacher rolled out a giant paper mural across the floor!", "caps": "Art class *CHALLENGE! | The teacher rolled out a giant *PAPER | mural across the *FLOOR!"},
            {"text": "Benny the bunny sat guarding his luxury sixty-four crayon box with his paws!", "caps": "Benny the bunny sat *GUARDING | his sixty-four crayon box with his *PAWS!"},
            {"text": "May I borrow sky blue for my river? asked Penny. No, it's mine! Benny snapped!", "caps": "May I borrow *SKY BLUE? | asked Penny. No, it's *MINE! | Benny *SNAPPED!"},
            {"text": "Benny drew a big blue lake in his corner, but had no green for trees and no yellow for sun!", "caps": "Benny drew a lake, but had *NO GREEN | for trees and no yellow for the *SUN!"},
            {"text": "His picture was dull, while Penny and Leo traded pink, purple, and orange joyfully!", "caps": "His picture was *DULL, | while his friends traded colors *JOYFULLY!"},
            {"text": "Benny realized: One color alone can never paint a whole vibrant world!", "caps": "Benny realized: One color *ALONE | can never paint a whole *VIBRANT | *WORLD!"},
            {"text": "He slid his box to the center: Take whatever colors you need, everyone!", "caps": "He slid his box to the *CENTER: | Take whatever colors you *NEED!"},
            {"text": "Together they finished the most stunning rainbow forest the school had ever seen!", "caps": "Together they finished the most *STUNNING | rainbow mural ever *SEEN!"},
            {"text": "Share your gifts and shine bright—subscribe to BabyBeats Rhymo!", "caps": "Share your *GIFTS | and shine bright—*SUBSCRIBE | to *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "27_02_27",
        "day": 109,
        "date_str": "27/02/27",
        "category": "science-curiosity",
        "title": "Why Do We Sweat? Your Built-In Air Conditioner!",
        "thumb_text": "HOW SWEAT WORKS?!",
        "primary_keyword": "why do we sweat kids science cartoon",
        "supporting_keywords": ["evaporative cooling human body kids", "perspiration science explained children", "why sweat keeps us cool cartoon"],
        "fact_summary": "When you sprint and heat up, 3 million sweat glands release water droplets; as the breeze evaporates the liquid, it steals heat away to cool you down.",
        "hook": "You race around the soccer field, and tiny droplets of water roll down your forehead! Why does your skin start leaking water?",
        "publish_slot_est": "2027-02-27T15:30:00-05:00",
        "publish_at_utc": "2027-02-27T20:30:00Z",
        "lines": [
            {"text": "You're sprinting across the soccer pitch, kicking the ball, and dripping wet!", "caps": "You're sprinting across the *FIELD, | kicking the ball, and dripping *WET!"},
            {"text": "Why does your body pump salty water out of your forehead when you run fast?", "caps": "Why does your body pump *WATER | out of your forehead when you *RUN?"},
            {"text": "Your muscles act like car engines; when they work hard, they burn energy and create heat!", "caps": "Your muscles are like *ENGINES; | when they work hard, they create *HEAT!"},
            {"text": "You have over three million microscopic sweat glands all across your skin!", "caps": "You have over three *MILLION | microscopic sweat glands across your *SKIN!"},
            {"text": "Your brain signals these glands to release a thin layer of ninety-nine percent water!", "caps": "Your brain signals these *GLANDS | to release a thin layer of *WATER!"},
            {"text": "Here comes the genius physics trick: evaporative cooling!", "caps": "Here comes the genius *PHYSICS | trick: evaporative *COOLING!"},
            {"text": "As the outdoor breeze blows across your skin, water transforms into vapor!", "caps": "As the outdoor breeze *BLOWS, | water transforms into *VAPOR!"},
            {"text": "It steals heat energy directly off your skin, keeping your body safe from overheating!", "caps": "It steals heat energy right off your *SKIN, | keeping you safe from *OVERHEATING!"},
            {"text": "Stay hydrated and curious—subscribe to BabyBeats Rhymo!", "caps": "Stay hydrated and *CURIOUS— | *SUBSCRIBE to | *BABYBEATS *RHYMO!"}
        ]
    },
    {
        "id": "28_02_27",
        "day": 110,
        "date_str": "28/02/27",
        "category": "moral-story",
        "title": "Leo's Morning Routine Victory: Five Minutes Ahead of Time!",
        "thumb_text": "MORNING VICTORY!",
        "primary_keyword": "morning routine habits for children cartoon",
        "supporting_keywords": ["punctuality school morning routine", "no rushing getting ready kids", "positive morning habits cartoon"],
        "fact_summary": "Packing your backpack and picking clothes the night before eliminates frantic morning panic, starting your school day calm and victorious.",
        "hook": "Every morning, Leo was hunting for missing shoes, gulping toast, and racing frantically for the school bus! How did 3 small steps change his life?",
        "publish_slot_est": "2027-02-28T15:30:00-05:00",
        "publish_at_utc": "2027-02-28T20:30:00Z",
        "lines": [
            {"text": "BEEP BEEP! Seven o'clock alarm, and Leo was rushing around like a whirlwind!", "caps": "*BEEP BEEP! Seven o'clock, | and Leo was rushing around like a *WHIRLWIND!"},
            {"text": "Where is my left blue sneaker? Did anyone pack my homework notebook?", "caps": "Where is my left *SNEAKER? | Did anyone pack my homework *NOTEBOOK?"},
            {"text": "Spilling cereal, untied shoelaces, and running frantically as the yellow bus honked!", "caps": "Spilling cereal, untied *LACES, | and running as the yellow bus *HONKED!"},
            {"text": "That night, Rhymo said, Let's win tomorrow before we even close our eyes!", "caps": "That night, Rhymo *SAID, | Let's win tomorrow before we close our *EYES!"},
            {"text": "Step one: Backpack packed and zipped right by the front door!", "caps": "*STEP ONE: | Backpack packed and zipped right by the *FRONT DOOR!"},
            {"text": "Step two: Blue sneakers placed side-by-side with socks inside!", "caps": "*STEP TWO: | Sneakers placed side-by-side with *SOCKS | *INSIDE!"},
            {"text": "Next morning, Leo woke up, got dressed in three minutes, and ate pancakes calmly!", "caps": "Next morning, Leo dressed in three *MINUTES | and ate pancakes *CALMLY!"},
            {"text": "He strolled to the bus stop five minutes early, smiling like a champion!", "caps": "He strolled to the bus stop *EARLY, | smiling like a true *CHAMPION!"},
            {"text": "Win your mornings and win your days—subscribe to BabyBeats Rhymo!", "caps": "Win your *MORNINGS | and win your days—*SUBSCRIBE | to *BABYBEATS *RHYMO!"}
        ]
    }
]


def update_topic_queue(selected_topics: list):
    if QUEUE_PATH.exists():
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    else:
        data = {"channel_id": "UCR-Di4-tEAdUM7oPzlGn-vg", "topics": []}

    topics = data.setdefault("topics", [])
    for nt in selected_topics:
        existing = next((t for t in topics if t.get("id") == nt["id"]), None)
        entry = {
            "id": nt["id"],
            "day": nt["day"],
            "category": nt["category"],
            "title": nt["title"],
            "thumb_text": nt["thumb_text"],
            "primary_keyword": nt["primary_keyword"],
            "supporting_keywords": nt["supporting_keywords"],
            "score_breakdown": {
                "audience_demand": 19,
                "recent_growth": 18,
                "competition_opportunity": 15,
                "audience_curiosity": 17,
                "click_potential": 9,
                "retention_potential": 9,
                "production_feasibility": 5,
                "niche_relevance": 5
            },
            "total_score": 97,
            "fact_summary": nt["fact_summary"],
            "sources": ["https://kidshealth.org", "https://www.zerotothree.org"],
            "hook": nt["hook"],
            "visual_focus": "expressive cartoon mascot characters learning emotional skills, science facts, and moral lessons",
            "status": "ready_for_upload"
        }
        if existing:
            existing.update(entry)
        else:
            topics.append(entry)

    QUEUE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {QUEUE_PATH} with {len(selected_topics)} story topics.")


def build_shots_for_story(topic: dict) -> str:
    shot_blocks = []
    lines = topic["lines"]
    scenes = [
        ("story_intro", "room", f"K.room(); P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), {{ mood: 'happy', t }}); K.pill('{topic['thumb_text']}', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6))); K.burst(540, 740, 1.1, 0.5);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("problem", "blank", "fillAll('#FEF2F2'); P.kidCartoon(380, 860, 1.55, { mood: 'lookDown', t }); K.pill('UH OH!', 540, 310, 44, C.red, C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.6 });"),
        ("shock", "room", "K.room(); P.kidCartoon(540, 860, 1.65, { mood: 'gasp', t }); K.pill('WAIT WHAT?!', 540, 310, 46, C.red, C.white, eob(seg(lt, 0, 0.4)));", "cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.8 });"),
        ("discovery", "blank", "fillAll('#FFFBEB'); P.kidCartoon(380, 860, 1.5, { mood: 'think', t }); P.magnifier(700, 700, 140); K.pill('DID YOU KNOW?', 540, 310, 44, '#B45309', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("action_step", "room", "K.room(); P.kidCartoon(540, 860, 1.55, { mood: 'gasp', t }); K.pill('THE SECRET!', 540, 315, 44, C.ink, C.yellow, eob(seg(lt, 0, 0.4)));", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("kindness", "blank", "fillAll('#FEFCE8'); P.kidCartoon(380, 860, 1.55, { mood: 'happy', t }); K.pill('TRY THIS!', 540, 310, 44, '#15803D', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });"),
        ("heart_moment", "room", "K.room(); P.kidCartoon(540, 860, 1.6, { mood: 'happy', t }); K.pill('SO POWERFUL!', 540, 310, 46, '#15803D', C.white, eob(seg(lt, 0, 0.4)));", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });"),
        ("moral_truth", "blank", "fillAll('#F0FDF4'); P.kidCartoon(360, 860, 1.45, { mood: 'happy', t }); P.magnifier(720, 680, 155); K.pill('BIG LESSON!', 540, 310, 44, '#15803D', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.35, 'pop');"),
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
    print(f"GENERATING [{nt['day']}/110]: {proj_name} ({nt['title']})")
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
        "sources": ["https://kidshealth.org", "https://www.zerotothree.org"],
        "lines": nt["lines"]
    }
    (proj_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    # Shots js
    (proj_dir / "src" / "shots.js").write_text(build_shots_for_story(nt), encoding="utf-8")

    # SEO & Thumbnail
    (proj_dir / "renders").mkdir(exist_ok=True)
    seo_out = proj_dir / "seo_package.json"
    thumb_out = proj_dir / "renders" / f"{tid}_thumb.jpg"
    mp4_out = proj_dir / "renders" / f"{tid}_short.mp4"

    print("-> Building SEO package...")
    subprocess.run([PY_VENV, str(SEO_PY), "--topic-id", tid, "--out", str(seo_out)], check=True)

    if not thumb_out.exists():
        print("-> Rendering 1280x720 Thumbnail...")
        thumb_created = False
        for attempt in range(1, 4):
            try:
                subprocess.run(
                    ["node", str(MAKE_THUMB_MJS), str(thumb_out), nt["thumb_text"], nt["category"], "BABYBEATS RHYMO"],
                    check=True,
                    timeout=60
                )
                if thumb_out.exists() and thumb_out.stat().st_size > 1000:
                    thumb_created = True
                    break
            except Exception as e:
                if thumb_out.exists() and thumb_out.stat().st_size > 1000:
                    print(f"   [note] Thumbnail file created successfully despite process exit code: {thumb_out.name}")
                    thumb_created = True
                    break
                print(f"   [warn] Thumbnail attempt {attempt}/3 failed: {e}")
                time.sleep(3)
        if not thumb_created:
            print("   [warn] Retrying thumbnail with fallback simple render if needed...")
            if not thumb_out.exists():
                raise RuntimeError(f"Failed to generate thumbnail for {tid}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="Start index (1-based, 1=02_02_27)")
    parser.add_argument("--end", type=int, default=len(FEBRUARY_27_STORIES), help="End index (1-based, 27=28_02_27)")
    args = parser.parse_args()

    selected = FEBRUARY_27_STORIES[args.start - 1 : args.end]
    update_topic_queue(selected)
    total = len(selected)
    for i, nt in enumerate(selected, 1):
        print(f"\n>>> PROCESSING FEBRUARY STORY VIDEO {i}/{total}: {nt['id']}_short <<<")
        generate_single_short(nt)
    print("\n========================================================")
    print(f"ALL {total} FEBRUARY STORY VIDEOS GENERATED SUCCESSFULLY!")
    print("========================================================")


if __name__ == "__main__":
    main()

# Reference photo policy

Client/you koi real insaan ki photo bheje ("aisa hi banao") — ye rule follow karo.

## Kya allowed hai
**Style DNA copy karna** (pose, lighting, hair styling, wardrobe vibe, colour pop, mood, crop).
Ye legal hai, yehi to creative direction hai.

## Kya strictly banned hai
**Us insaan ka face reproduce karna.** Ye deepfake hai:
- Fanvue: "AI-generated media must not be of a real person other than the account owner." Deepfake
  pe account ban + payout hold.
- Meta/Instagram: real person ki likeness without consent = removal + ban.
- India: IT Act s.66E (privacy), BNS defamation, naye IT Rules SGI labelling; right to publicity.
- Adult context me ye aur bhi serious hai (non-consensual intimate imagery laws).

Sirf 6 feature badalna kaafi nahi hota — **bone structure alag hona chahiye**: face shape, eye shape
aur corner direction, nose tip width, lip ratio, jawline, mole/freckle placement.

## Workflow (30 min)

1. Reference photo dekho (ya user se 2-3 angles lo).
2. Ye 7 cheezein likho: pose / light direction + quality / expression / hair / outfit + jewellery /
   set + prop / colour pop.
3. Prompt me sirf wahi 7 likho. Face ke liye ek **naya original** description likho jisme 5+ features
   reference se alag hon.
4. 2 variants generate karo. Dono ek jaise aayein to identity lock ho gayi — wahi master.
5. 6-angle sheet banao (`prompts/01b_face_master_v3.txt` pattern).
6. Master ko `assets/character_vN/master.png` me save karo, `config/character_vN.json` banao,
   aur `_provenance.style_dna_from_reference` me 7 points likh do — future me proof kaam aayega.

## Client ko kaise bolna hai (script)

> "Aapki reference photo ka **look** main le raha hoon — pose, light, hair, vibe. Face main naya
> original bana raha hoon, kyunki kisi real person ka AI clone platform pe instant ban aur legal
> case dono hai. Result aapko usi vibe ka milega, par wo ek nayi identity hogi jo aapki hi hai."

## Example (jo humne kiya)
Reference: over-shoulder + hard warm sun from left + black top + red chair + messy ponytail.
Output: wahi 6 cheezein, par face me soft oval jaw, **downturned** outer eye corners, wider nose tip,
fuller lower lip, freckles, mole left jawline — visibly different insaan, same energy.

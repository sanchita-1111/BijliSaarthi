import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
LOGO = APP_DIR / "bijlisaarthi_logo.png"
PROFILE_FILE = APP_DIR / "bijlisaarthi_profile.json"

st.set_page_config(page_title="BijliSaarthi", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

# -----------------------------
# Persistent local profile
# -----------------------------
def load_profile():
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_profile(profile):
    try:
        PROFILE_FILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False

profile = load_profile()

# -----------------------------
# Consumer-first styling
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp{background:radial-gradient(circle at 5% 0%,rgba(255,173,80,.18),transparent 27%),radial-gradient(circle at 95% 10%,rgba(55,211,154,.15),transparent 25%),linear-gradient(135deg,#071225,#0b1830 48%,#081827);color:#f8fafc;}
.main .block-container{max-width:1200px;padding:1rem 1.2rem 5rem;}
header[data-testid="stHeader"]{background:transparent;} [data-testid="stToolbar"],#MainMenu,footer{display:none;}
.hero{border-radius:30px;padding:1.6rem 1.6rem 1.5rem;background:linear-gradient(135deg,rgba(255,255,255,.13),rgba(255,255,255,.035));border:1px solid rgba(255,255,255,.12);box-shadow:0 24px 70px rgba(0,0,0,.28);animation:rise .6s ease-out;}
.hero-title{font-family:'Manrope';font-size:clamp(2.1rem,5vw,4.2rem);font-weight:800;letter-spacing:-.055em;line-height:1.03;margin:0;color:#fff;}
.hero-sub{font-size:1.08rem;color:#d9e4f3;max-width:850px;margin:.7rem 0 0;line-height:1.55;}
.pill{display:inline-block;padding:.42rem .72rem;margin:.8rem .35rem 0 0;border-radius:999px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.13);font-size:.82rem;}
.section{margin-top:1.1rem;padding:1.25rem;border-radius:25px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.1);box-shadow:0 14px 40px rgba(0,0,0,.18);animation:rise .5s ease-out;}
.section h2{font-family:'Manrope';margin:.1rem 0 .3rem;font-size:1.5rem;}.muted{color:#b9c5d7}.small{color:#aebbd0;font-size:.86rem}
.metric{border-radius:22px;padding:1.05rem;background:#fff;color:#172033;min-height:150px;box-shadow:0 14px 36px rgba(0,0,0,.2);}
.metric .label{font-size:.86rem;color:#657083}.metric .value{font-family:'Manrope';font-size:2.15rem;font-weight:800;margin-top:.2rem;color:#111827 !important;text-shadow:none}.metric .note{font-size:.82rem;color:#596579;margin-top:.25rem}
.good{border-left:5px solid #37d39a;background:rgba(55,211,154,.11);padding:.9rem 1rem;border-radius:14px}.warn{border-left:5px solid #ffbd4a;background:rgba(255,189,74,.12);padding:.9rem 1rem;border-radius:14px}.alert{border-left:5px solid #ff6b6b;background:rgba(255,107,107,.12);padding:.9rem 1rem;border-radius:14px}
.tip{background:linear-gradient(135deg,rgba(255,174,74,.14),rgba(55,211,154,.08));border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:1rem;margin:.5rem 0;}
.stButton>button{border-radius:14px;min-height:45px;font-weight:700;border:1px solid rgba(255,255,255,.13)}
.stTextInput input,.stNumberInput input,.stDateInput input,.stSelectbox div[data-baseweb="select"]{border-radius:12px;}
.conf{display:inline-block;padding:.32rem .65rem;border-radius:999px;background:rgba(55,211,154,.14);border:1px solid rgba(55,211,154,.25);font-size:.78rem;margin:.2rem}
.scan-card{border-radius:20px;background:rgba(255,255,255,.06);padding:1rem;border:1px solid rgba(255,255,255,.09)}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Estimation
# -----------------------------
APPLIANCES={
    "Fan":(65,6,"Switch off fans in empty rooms and use them only where someone is present."),
    "LED bulbs":(9,6,"Use daylight when possible and switch off lights in empty rooms."),
    "Refrigerator":(140,24,"Keep the door closed and leave ventilation space around the refrigerator."),
    "TV":(90,4,"Avoid leaving the TV on in an empty room; switch it off after use."),
    "Phone chargers":(8,2,"Unplug chargers after charging when practical."),
    "Air conditioner":(1200,4,"Avoid cooling empty rooms and use a moderate temperature setting."),
    "Cooler":(180,6,"Use the cooler only when the room needs it."),
    "Washing machine":(500,.5,"Batch full loads instead of running partial loads."),
    "Geyser":(2000,.5,"Use a timer and switch the geyser off after the required heating period."),
    "Water pump":(750,1,"Avoid unnecessary pumping and check for leaks or overflow."),
    "Iron":(1000,.3,"Batch ironing into fewer sessions and switch the iron off between use."),
    "Microwave":(1200,.2,"Use only for the required heating time."),
    "Computer/Laptop":(120,5,"Use sleep mode during breaks and switch off when finished."),
}

def appliance_daily_kwh(selected,qty,hours):
    return sum(APPLIANCES[a][0]*max(1,int(qty.get(a,1)))*max(0,float(hours.get(a,APPLIANCES[a][1])))/1000 for a in selected)

def estimate(prev,curr,units,last_bill,budget,bill_days,days_left,selected,qty,hours):
    """Estimate using the latest bill itself instead of a guessed tariff.

    Electricity tariffs vary by DISCOM, state, consumer category and usage slab.
    Therefore the consumer is not asked to guess a ₹/kWh value. When both bill
    amount and units are available, BijliSaarthi derives an effective billed rate
    as bill amount / units and uses that household-specific rate for planning.
    """
    meter_units=(curr-prev) if prev is not None and curr is not None and curr>=prev and curr>0 else None
    base=meter_units if meter_units and meter_units>0 else units
    appliance_daily=appliance_daily_kwh(selected,qty,hours) if selected else 0
    hist_daily=base/max(1,bill_days) if base and base>0 else None
    daily=(.72*hist_daily+.28*appliance_daily) if hist_daily is not None and appliance_daily>0 else (hist_daily or max(appliance_daily,.5))
    cycle_units=max(0,daily*max(1,bill_days))
    rem_units=max(0,daily*max(1,days_left))
    effective_rate=(last_bill/units) if last_bill>0 and units>0 else 0
    projected_bill=cycle_units*effective_rate if effective_rate>0 else last_bill
    bill=.65*projected_bill+.35*last_bill if last_bill and last_bill>0 else projected_bill
    gap=budget-bill
    save_rs=max(0,-gap)
    save_kwh=save_rs/max(effective_rate,.01) if effective_rate>0 else 0
    return {"meter_units":meter_units,"daily":daily,"cycle_units":cycle_units,"remaining_units":rem_units,"bill":bill,"gap":gap,"save_rs":save_rs,"save_kwh":save_kwh,"effective_rate":effective_rate}

# -----------------------------
# One-time household setup
# -----------------------------
if "profile" not in st.session_state:
    st.session_state.profile=profile

if not st.session_state.profile.get("setup_complete"):
    st.markdown('<div class="section"><h2>👋 Welcome to BijliSaarthi</h2><div class="muted">Set your household profile once. BijliSaarthi saves these preferences locally on this computer so you do not have to enter them every month.</div></div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        name=st.text_input("Your name",value=profile.get("name",""))
        mobile=st.text_input("Mobile number (optional)",value=profile.get("mobile",""))
        budget0=st.number_input("Usual monthly electricity budget (₹)",min_value=0.0,value=float(profile.get("budget",2000)),step=100.0)
    with b:
        people0=st.number_input("People at home",min_value=1,max_value=20,value=int(profile.get("people",4)),step=1)
        selected0=st.multiselect("Appliances you have",list(APPLIANCES),default=profile.get("selected",["Fan","LED bulbs","Refrigerator","TV","Phone chargers"]))
    if st.button("💾 Save my household once",type="primary",use_container_width=True):
        prof={"setup_complete":True,"name":name.strip(),"mobile":mobile.strip(),"budget":budget0,"people":people0,"selected":selected0,"qty":{a:1 for a in selected0},"hours":{a:APPLIANCES[a][1] for a in selected0},"last_bill":{},"updated":datetime.now().isoformat()}
        save_profile(prof); st.session_state.profile=prof; st.success("Saved. Next time, enter only the new bill values."); st.rerun()
    st.stop()

profile=st.session_state.profile
selected=profile.get("selected",[])
qty_map=profile.get("qty",{a:1 for a in selected})
hours_map=profile.get("hours",{a:APPLIANCES[a][1] for a in selected})
budget=float(profile.get("budget",2000)); people=int(profile.get("people",4))
last_saved=profile.get("last_bill",{}) or {}

# -----------------------------
# Header
# -----------------------------
logo_col, hero_col = st.columns([1.2,5],vertical_alignment="center")
with logo_col:
    if LOGO.exists(): st.image(str(LOGO),use_container_width=True)
with hero_col:
    st.markdown('''<div class="hero"><div class="hero-title">Bill samjho, bijli bachao — kharcha ghatao, budget sambhalo!</div><div class="hero-sub">Enter your electricity bill values once for the current cycle. Saarthi remembers your household, estimates the next bill, and gives a practical saving plan. You can edit any value before trusting the result.</div><span class="pill">🇮🇳 Made for Indian households</span><span class="pill">🧾 Simple bill entry</span><span class="pill">🏠 One-time household setup</span><span class="pill">💰 Budget-first</span><span class="pill">🤖 Saarthi</span></div>''',unsafe_allow_html=True)

# -----------------------------
# Manual bill details — only thing to change monthly
# -----------------------------
st.markdown('<div class="section"><h2>🧾 Enter this month’s bill</h2><div class="muted">Enter the values printed on your electricity bill. Your household profile is already saved. You can change any value if needed.</div></div>',unsafe_allow_html=True)

fields={}

# -----------------------------
# Editable bill details — only thing to change monthly
# -----------------------------
st.markdown('<div class="section"><h2>🧾 Check once, then calculate</h2><div class="muted">These are the bill values you can change for the current cycle. Your household profile stays saved.</div></div>',unsafe_allow_html=True)

p_default=float(fields.get("previous_reading") if fields.get("previous_reading") is not None else (last_saved.get("current_reading") or 0))
c_default=float(fields.get("current_reading") or 0)
u_default=float(fields.get("units") or 0)
a_default=float(fields.get("amount") or last_saved.get("amount") or 0)

c1,c2,c3,c4=st.columns(4)
with c1: prev=st.number_input("Previous meter reading (kWh)",min_value=0.0,value=p_default,step=1.0,key="prev_v3")
with c2: curr=st.number_input("Current meter reading (kWh)",min_value=0.0,value=c_default,step=1.0,key="curr_v3")
with c3: units=st.number_input("Units used on this bill (kWh)",min_value=0.0,value=u_default,step=1.0,key="units_v3")
with c4: last_bill=st.number_input("Bill amount (₹)",min_value=0.0,value=a_default,step=10.0,key="amt_v3")

x1,x2,x3=st.columns(3)
with x1: bill_days=st.number_input("Billing days",min_value=1,max_value=90,value=int(last_saved.get("bill_days",30)),step=1,key="days_v3")
with x2: days_left=st.number_input("Approx. days until next bill",min_value=1,max_value=45,value=int(last_saved.get("days_left",10)),step=1,key="left_v3")
with x3: fixed=st.number_input("Fixed/other charges (₹)",min_value=0.0,value=float(last_saved.get("fixed",100)),step=10.0,key="fixed_v3")

if prev and curr and curr<prev: st.error("Current meter reading cannot be lower than the previous reading. Please correct it.")

p_default=float(last_saved.get("current_reading") or 0)
c_default=0.0
u_default=float(last_saved.get("units") or 0)
a_default=float(last_saved.get("amount") or 0)

c1,c2,c3,c4=st.columns(4)
with c1: prev=st.number_input("Previous meter reading (kWh)",min_value=0.0,value=p_default,step=1.0,key="prev_clean")
with c2: curr=st.number_input("Current meter reading (kWh)",min_value=0.0,value=c_default,step=1.0,key="curr_clean")
with c3: units=st.number_input("Units used on this bill (kWh)",min_value=0.0,value=u_default,step=1.0,key="units_clean")
with c4: last_bill=st.number_input("Bill amount (₹)",min_value=0.0,value=a_default,step=10.0,key="amt_clean")

x1,x2=st.columns(2)
with x1: bill_days=st.number_input("Billing days",min_value=1,max_value=90,value=int(last_saved.get("bill_days",30)),step=1,key="days_clean")
with x2: days_left=st.number_input("Approx. days until next bill",min_value=1,max_value=45,value=int(last_saved.get("days_left",10)),step=1,key="left_clean")

if prev and curr and curr<prev: st.error("Current meter reading cannot be lower than the previous reading. Please correct it.")

if last_bill>0 and units>0:
    effective_rate_preview=last_bill/units
    st.caption(f"Automatic bill-based rate: approximately ₹{effective_rate_preview:.2f}/kWh. This is calculated from your actual bill — you do not need to guess a tariff.")

with st.expander("✏️ Change saved household details (only if something changed)"):
    e1,e2=st.columns(2)
    with e1:
        new_name=st.text_input("Name",value=profile.get("name",""))
        new_budget=st.number_input("Monthly budget (₹)",min_value=0.0,value=budget,step=100.0)
    with e2:
        new_people=st.number_input("People at home",min_value=1,max_value=20,value=people,step=1)
        new_selected=st.multiselect("Appliances",list(APPLIANCES),default=selected)
    if st.button("Save changes to my household",use_container_width=True):
        profile.update({"name":new_name.strip(),"budget":new_budget,"people":new_people,"selected":new_selected,"qty":{a:profile.get("qty",{}).get(a,1) for a in new_selected},"hours":{a:profile.get("hours",{}).get(a,APPLIANCES[a][1]) for a in new_selected},"updated":datetime.now().isoformat()})
        save_profile(profile); st.session_state.profile=profile; st.success("Household profile updated. You will not need to repeat it next month."); st.rerun()

# Optional per-appliance detail is hidden until user wants to edit it.
with st.expander("🏠 Fine-tune appliance use (optional)"):
    if selected:
        cols=st.columns(2)
        for i,a in enumerate(selected):
            with cols[i%2]:
                qty_map[a]=st.number_input(f"{a} quantity",1,20,int(qty_map.get(a,1)),1,key=f"qtyv3_{a}")
                hours_map[a]=st.number_input(f"{a} hours/day",0.0,24.0,float(hours_map.get(a,APPLIANCES[a][1])),.25,key=f"hrsv3_{a}")
    if st.button("Save appliance settings",use_container_width=True):
        profile["qty"]=qty_map; profile["hours"]=hours_map; save_profile(profile); st.session_state.profile=profile; st.success("Saved.")

# -----------------------------
# Calculate and persist last bill
# -----------------------------
if st.button("💰 Calculate my next bill estimate",type="primary",use_container_width=True):
    if prev and curr and curr<prev:
        st.error("Please correct the meter readings first.")
    elif not last_bill and not units and not (prev and curr):
        st.error("Please enter the bill amount, units, or both meter readings.")
    else:
        result=estimate(prev,curr,units,last_bill,budget,bill_days,days_left,selected,qty_map,hours_map)
        st.session_state.result=result
        profile["last_bill"]={"current_reading":curr,"amount":last_bill,"units":units,"bill_days":bill_days,"days_left":days_left,"fixed":fixed,"saved_at":datetime.now().isoformat()}
        save_profile(profile)

result=st.session_state.get("result")
if result:
    st.markdown('<div class="section"><h2>💰 Your BijliSaarthi estimate</h2><div class="muted">A budgeting estimate based on your confirmed bill data and saved household profile.</div></div>',unsafe_allow_html=True)
    r1,r2,r3,r4=st.columns(4)
    with r1: st.markdown(f'<div class="metric"><div class="label">Estimated next bill</div><div class="value">₹{result["bill"]:,.0f}</div><div class="note">planning estimate</div></div>',unsafe_allow_html=True)
    with r2:
        if result["gap"]>=0: st.markdown(f'<div class="metric"><div class="label">Budget remaining</div><div class="value">₹{result["gap"]:,.0f}</div><div class="note">within your ₹{budget:,.0f} target</div></div>',unsafe_allow_html=True)
        else: st.markdown(f'<div class="metric"><div class="label">Above budget</div><div class="value">₹{abs(result["gap"]):,.0f}</div><div class="note">amount to control</div></div>',unsafe_allow_html=True)
    with r3: st.markdown(f'<div class="metric"><div class="label">Projected cycle use</div><div class="value">{result["cycle_units"]:,.1f} kWh</div><div class="note">estimated billing-cycle use</div></div>',unsafe_allow_html=True)
    with r4: st.markdown(f'<div class="metric"><div class="label">Next {days_left} days</div><div class="value">{result["remaining_units"]:,.1f} kWh</div><div class="note">estimated remaining use</div></div>',unsafe_allow_html=True)

    if result["gap"]>=0:
        st.markdown(f'<div class="good">🎉 You are about <b>₹{result["gap"]:,.0f}</b> inside your budget. Keep the same usage pattern and watch the meter.</div>',unsafe_allow_html=True)
    else:
        daily_save=result["save_kwh"]/max(1,days_left)
        st.markdown(f'<div class="alert">⚠️ Your projection is about <b>₹{abs(result["gap"]):,.0f}</b> above budget. To target your budget, try to reduce roughly <b>{daily_save:.2f} kWh/day</b> until the next bill.</div>',unsafe_allow_html=True)

    st.markdown("### 🌱 Your personal saving plan")
    for i,a in enumerate(selected[:8],1): st.markdown(f'<div class="tip"><b>{i}. {a}</b><br>{APPLIANCES[a][2]}</div>',unsafe_allow_html=True)
    if result["gap"]<0:
        st.markdown(f'<div class="warn"><b>Budget target:</b> focus on controllable use first. Your planning target is about <b>{result["save_kwh"]/max(1,days_left):.2f} kWh/day</b> of reduction. This is not a guaranteed saving.</div>',unsafe_allow_html=True)

# -----------------------------
# Saarthi chat
# -----------------------------
st.markdown('<div class="section"><h2>🤖 Ask Saarthi</h2><div class="muted">Try: “Why is my bill high?”, “How much should I save?”, “Which appliance should I watch?”, or “What does my bill mean?”</div></div>',unsafe_allow_html=True)
for who,msg in st.session_state.get("chat",[]):
    st.markdown(f'<div class="tip"><b>{who}:</b> {msg}</div>',unsafe_allow_html=True)
q=st.chat_input("Ask Saarthi…")
if q:
    st.session_state.setdefault("chat",[]).append(("You",q))
    ql=q.lower()
    r=st.session_state.get("result")
    if "why" in ql and "bill" in ql:
        ans=(f"Your current estimate is ₹{r['bill']:,.0f}. It is driven mainly by your recent consumption pace and the effective cost calculated from the bill values you entered." if r else "Enter your bill values first and I’ll explain the estimate.")
    elif "save" in ql or "reduce" in ql:
        ans=(f"Your current target is about {r['save_kwh']/max(1,days_left):.2f} kWh/day of reduction until the next bill." if r and r['gap']<0 else "Your estimate is within budget. Keep unused appliances off and watch the meter.")
    elif "rate" in ql or "tariff" in ql:
        ans=(f"Your bill-based effective rate is about ₹{r['effective_rate']:.2f}/kWh. This is calculated automatically from the bill amount and units you entered." if r and r['effective_rate']>0 else "Enter both the bill amount and units used, and I will calculate the effective bill-based rate automatically.")
    else:
        ans="I can explain your estimate, budget gap, remaining days, and appliance-saving plan. Ask me what is making the bill high or how much you should save."
    st.session_state["chat"].append(("Saarthi",ans)); st.rerun()

st.markdown("---")
st.caption("BijliSaarthi • Household electricity budgeting assistant • Estimates are for planning and are not official utility bills. Electricity tariffs vary by DISCOM, state, consumer category and usage slab.")

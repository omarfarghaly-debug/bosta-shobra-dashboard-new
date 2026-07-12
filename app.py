import streamlit as st
import pandas as pd
import numpy as np

# 1. إعدادات الصفحة والتنسيق بالألوان (الأحمر والأبيض) لشركة بوسطة
st.set_page_config(page_title="Bosta Shobra WH Dashboard", page_icon="🚚", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .title-box {
        background-color: #E30613; 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 25px;
    }
    .title-box h1 { color: white !important; font-family: 'Arial'; font-size: 32px; margin: 0; }
    .metric-box {
        background-color: #f8f9fa;
        border-left: 5px solid #E30613;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .stButton>button {
        background-color: #E30613;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 24px;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #b3050f; color: white; }
    </style>
""", unsafe_allow_html=True)

# العنوان الترحيبي باللون الأحمر والأبيض
st.markdown('<div class="title-box"><h1>Welcome on Bosta shobra WH</h1></div>', unsafe_allow_html=True)

# اسم ملف البيانات الافتراضي المرفوع بجانب الكود
file_path = "Attempts_Export_2026-07-12-1783889404621.xlsx"

try:
    df = pd.read_excel(file_path)
except Exception as e:
    st.error("خطأ: لم يتم العثور على ملف البيانات الأصلي. تأكد من رفعه في نفس المجلد وتسميته بدقة:")
    st.code(file_path)
    st.stop()

# --- 📁 الأيقونة الأساسية الأولى: تحميل الملف الأصلي عند الضغط ---
st.subheader("📁 Delivery Performance")
with open(file_path, "rb") as file:
    st.download_button(
        label="📥 اضغط هنا لتحميل ملف البيانات الأصلي",
        data=file,
        file_name="Attempts_Export_Original.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")

# --- 🛠️ معالجة البيانات وتحضير الحسابات المطلوبة ---

# 1. شحنات ذات قيمة أو بدون قيمة (مع تلبية الشروط المطلوبة)
df['Cod Amount'] = pd.to_numeric(df['Cod Amount'], errors='coerce').fillna(0)

def classify_value(cod):
    if cod > 0:
        return "💰 شحنة ذات قيمة مالية"
    else:
        # يظهر بصورتين (0 أو N/A) وبجوارها علامة (-)
        return "⚪ بدون قيمة (0 / N/A) [-]"

df['Value_Status'] = df['Cod Amount'].apply(classify_value)

# 2. حساب النسب الإحصائية لكل ساعي (Star)
star_stats = df.groupby('Star Name').agg(
    Total_Shipments=('Tracking ID', 'count'),
    Succeeded_Shipments=('State', lambda x: (x == 'Succeeded').sum()),
    In_Progress_Shipments=('State', lambda x: (x == 'In Progress').sum()),
    Cancel_Count=('Exception Reason', lambda x: x.str.contains('Cancellation|الغاء', case=False, na=False).sum())
).reset_index()

# حساب نسب الأداء (المناديب) Succeeded / total
star_stats['Delivery_Performance (%)'] = (star_stats['Succeeded_Shipments'] / star_stats['Total_Shipments'] * 100).round(2)
star_stats['In_Progress (%)'] = (star_stats['In_Progress_Shipments'] / star_stats['Total_Shipments'] * 100).round(2)
star_stats['Cancellation (%)'] = (star_stats['Cancel_Count'] / star_stats['Total_Shipments'] * 100).round(2)

# --- 📊 عرض البيانات داخل لوحة التحكم ---

st.header("📊 أداء المناديب والشحنات (Star Performance Analysis)")

# القائمة المنسدلة لاختيار مندوب محدد أو رؤية الكل
selected_star = st.selectbox("اختر اسم المندوب (Star Name) لاستعراض تفاصيله كاملة:", ["عرض أداء الكل"] + list(star_stats['Star Name'].unique()))

if selected_star != "عرض أداء الكل":
    # تصفية البيانات للمندوب المحدد فقط
    star_df = df[df['Star Name'] == selected_star]
    star_row = star_stats[star_stats['Star Name'] == selected_star].iloc[0]
    
    # مربعات الإحصاء الحيوية للمندوب
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-box"><h4>إجمالي الشحنات المستلمة</h4><h2>{star_row["Total_Shipments"]}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-box"><h4>نسبة النجاح (Succeeded)</h4><h2>{star_row["Delivery_Performance (%)"]}%</h2></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-box"><h4>شحنات قيد التنفيذ (In Progress)</h4><h2>{star_row["In_Progress_Shipments"]} ({star_row["In_Progress (%)"]}%)</h2></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-box"><h4>شحنات تم إلغاؤها</h4><h2>{star_row["Cancel_Count"]} ({star_row["Cancellation (%)"]}%)</h2></div>', unsafe_allow_html=True)

    col_details_1, col_details_2 = st.columns(2)
    
    with col_details_1:
        # عرض الأسباب وترتيبها من الأعلى للأقل مع تحديد مستوى التكرار
        st.subheader("⚠️ جميع أسباب عدم التسليم وترتيبها تنازلياً")
        reasons = star_df['Exception Reason'].value_counts().reset_index()
        reasons.columns = ['السبب المستخدم', 'العدد']
        
        if not reasons.empty:
            # إضافة علامة تمييز إذا كان التكرار عالٍ
            reasons['مستوى الاستخدام'] = reasons['العدد'].apply(lambda x: "🚨 عالي جداً!" if x > 10 else "⚠️ عالي" if x > 3 else "✅ طبيعي")
            st.dataframe(reasons, use_container_width=True)
            
            # إظهار السبب الأكثر استخداماً منفصلاً
            st.info(f"💡 **السبب الأكثر استخداماً لهذا المندوب هو:** {reasons.iloc[0]['السبب المستخدم']}")
        else:
            st.success("🎉 ممتاز! لا توجد أسباب فشل أو تأجيل مسجلة لهذا المندوب (كل الشحنات ناجحة بنسبة 100%).")
            
    with col_details_2:
        # فحص الشحنات ذات القيمة وبدون قيمة المسندة للمندوب
        st.subheader("💰 تصنيف قيمة الشحنات المالية للمندوب")
        val_counts = star_df['Value_Status'].value_counts().reset_index()
        val_counts.columns = ['حالة الشحنة', 'عدد الشحنات']
        st.dataframe(val_counts, use_container_width=True)

else:
    # الشاشة العامة لمقارنة جميع المناديب واكتشاف الأعلى إلغاءً أو أداءً
    st.subheader("🏆 لوحة التحكم المقارنة للمستودع")
    
    tab1, tab2 = st.tabs(["🔝 ترتيب المناديب حسب نسبة النجاح والأداء", "❌ المناديب الأكثر استخداماً لحالات الإلغاء"])
    
    with tab1:
        st.markdown("💡 *الجدول التالي مرتب من المندوب الأعلى كفاءة ونسبة نجاح إلى الأقل:*")
        sorted_perf = star_stats[['Star Name', 'Total_Shipments', 'Succeeded_Shipments', 'Delivery_Performance (%)', 'In_Progress_Shipments', 'In_Progress (%)']].sort_values(by='Delivery_Performance (%)', ascending=False)
        st.dataframe(sorted_perf, use_container_width=True)
        
    with tab2:
        st.markdown("💡 *الجدول التالي يوضح أعلى النجوم (Stars) استخداماً للإلغاءات والنسب المئوية الخاصة بهم:*")
        sorted_cancel = star_stats[['Star Name', 'Total_Shipments', 'Cancel_Count', 'Cancellation (%)']].sort_values(by='Cancel_Count', ascending=False)
        st.dataframe(sorted_cancel, use_container_width=True)
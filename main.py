import streamlit as st
import sqlite3
import os
import cv2
from PIL import Image
import io

DB_PATH = "word_data.db" 
IMAGE_FOLDER = "Images"

st.set_page_config(page_title="VLDL Mural Name Finder", page_icon="🎮")

def search_combination(query, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    search_words = query.split()
    search_length = len(search_words)

    cursor.execute("SELECT DISTINCT image_name FROM words WHERE word LIKE ?", (f"%{search_words[0]}%",))
    matching_images = cursor.fetchall()
    found_results = []

    for (image_name,) in matching_images:
        cursor.execute("SELECT word, left, top, width, height FROM words WHERE image_name = ?", (image_name,))
        words_data = cursor.fetchall()

        word_list = [{"word": w[0], "left": w[1], "top": w[2], "width": w[3], "height": w[4]} for w in words_data]
        
        for i in range(len(word_list) - search_length + 1):
            match = all(word_list[i + j]['word'].lower() == search_words[j].lower() for j in range(search_length))
            if match:
                found_results.append((image_name, word_list[i:i+search_length]))
                break
    conn.close()
    return found_results

def get_image_for_download(image_path, matched_words, query):
    """Process and return the image as BytesIO for download."""
    output_image = draw_combined_bounding_boxes(image_path, matched_words, query)
    output_image_rgb = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(output_image_rgb)
    img_bytes = io.BytesIO()
    pil_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def draw_combined_bounding_boxes(image_path, matched_words, query):
    image = cv2.imread(image_path)
    image_copy = image.copy()
    left = min(word['left'] for word in matched_words)
    top = min(word['top'] for word in matched_words)
    right = max(word['left'] + word['width'] for word in matched_words)
    bottom = max(word['top'] + word['height'] for word in matched_words)

    cv2.rectangle(image_copy, (left, top-20), (right, bottom), (0, 255, 0), 5)
    cv2.putText(image_copy, f"'{query}' Found!", (left, top - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return image_copy

st.title("🎮 VLDL Mural Wall Name Finder 🏰")
st.subheader("You have entered the realm of legends, traveler")

st.write("""
Type your name below, and watch as we scour these digital halls to find where you've been immortalized. No more squinting at high-res images! This is your gateway to locating your rightful spot among the heroes who powered up VLDL's greatest leap forward.
""")

search_query = st.text_input("🔍 **Enter your name or text to seek in the VLDL's Mural Wall:**")

if search_query:
    st.info(f"✨ On the hunt for '**{search_query}**'... Keep your eyes peeled!")
    with st.spinner("Searching the mural..."):
        results = search_combination(search_query, DB_PATH)

    if results:
        st.success(f"🎉 Victory! Found {len(results)} location(s) on the mural.")
        st.warning(f"❓ Found word combo is enclosed in a green box in the below image/s.")
        for image_name, matched_words in results:
            image_path = os.path.join(IMAGE_FOLDER, image_name)
            if os.path.exists(image_path):
                with st.spinner(f"🖌️ Highlighting your name..."):
                    output_image = draw_combined_bounding_boxes(image_path, matched_words, search_query)
                    output_image_rgb = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)

                # Display full-res image
                st.image(output_image_rgb, caption=f"Mural Match in: {image_name}")

                # Generate download button for each image
                if st.button(f"Prepare Download for {image_name}", key=f"prep_{image_name}"):
                    with st.spinner(f"Processing {image_name}..."):
                        # Process the image to create bounding boxes and prepare the BytesIO object
                        image_bytes = get_image_for_download(image_path, matched_words, search_query)
                        st.download_button(
                            label="Download Full Res Image",
                            data=image_bytes,
                            file_name=f"{image_name}_match.png",
                            mime="image/png",
                            key=f"download_{image_name}"
                        )
                st.markdown("---")

    else:
        st.error("No match found. Try a different spelling or another search.")
else:
    st.info("⏳ Enter a name above and let's see where you appear on the mural!")

st.markdown("---")
st.caption("VLDL Mural Wall Name Finder - Made with ❤️ for Viva La Dirt League fans.")
st.caption("Crafted with care by [JairajJangle](https://github.com/JairajJangle)")
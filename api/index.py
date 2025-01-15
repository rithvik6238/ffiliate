from gradio_client import Client, handle_file

try:
    client = Client("franciszzj/Leffa")
    result = client.predict(
        src_image_path=handle_file('https://levihsu-ootdiffusion.hf.space/file=/tmp/gradio/aa9673ab8fa122b9c5cdccf326e5f6fc244bc89b/model_8.png'),
        ref_image_path=handle_file('https://levihsu-ootdiffusion.hf.space/file=/tmp/gradio/17c62353c027a67af6f4c6e8dccce54fba3e1e43/048554_1.jpg'),
        ref_acceleration=False,
        step=30,
        scale=2.5,
        seed=42,
        vt_model_type="viton_hd",
        vt_garment_type="upper_body",
        vt_repaint=False,
        api_name="/leffa_predict_vt"
    )
    print(result)
except Exception as e:
    print(f"An error occurred: {e}")

import resend
# 全局设置API_KEY（建议通过环境变量配置）
resend.api_key ="re_PwfckyA7_9KYJLYS4v5TXQdA7gFtKRtJt"

def send_email(to_email: str, content: str, subject: str = "ArXiv论文总结"):
    """
    发送HTML邮件
    :param to_email: 目标邮箱地址
    :param content: HTML格式邮件内容
    :param subject: 邮件主题
    """
    params = {
        "from": "ArXiv论文助手 <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": content
    }
    
    try:
        # 修正后的API调用方式
        email = resend.Emails.send(params)
        print(f"邮件发送成功: {email}")
        return email
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return None


if __name__ == "__main__":
    # 示例用法
    to_email = "xy_wbfq@163.com"
    content = "<strong>ArXiv论文总结测试邮件</strong>"
    send_email(to_email, content)
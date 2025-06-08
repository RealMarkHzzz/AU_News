from content_analysis.analyzer import ContentAnalyzer

def test_analyzer():
    """测试内容分析器"""
    analyzer = ContentAnalyzer()
    
    # 测试文章
    sample_article = {
        "title": "New Policy for International Students in Adelaide",
        "content": """
        The Australian government has announced a new policy that will benefit international students,
        particularly Chinese students in Adelaide. The policy aims to improve safety and accommodation
        options for students, while also providing more part-time job opportunities.
        
        University officials have welcomed this change, saying it will help attract more students from China
        and other countries. The visa process will also be simplified according to the announcement.
        """
    }
    
    result = analyzer.analyze_article(sample_article["title"], sample_article["content"])
    
    print("\n分析结果:")
    print(f"相关性得分: {result['relevance_score']:.2f}")
    print(f"情感倾向: {result['sentiment']:.2f}")
    print(f"匹配关键词: {', '.join(result['matched_keywords'])}")

if __name__ == "__main__":
    test_analyzer()
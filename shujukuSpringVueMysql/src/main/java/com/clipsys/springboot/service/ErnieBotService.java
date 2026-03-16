package com.clipsys.springboot.service;

import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;


@Service
public class ErnieBotService {

    private static final String API_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-3.5-8k-preview";
    private static final String ACCESS_TOKEN = "24.53c8a8bd04c4287a4a1262a152aab67c.2592000.1727576486.282335-112504089";
//    x private static final String ACCESS_TOKEN = "24.b9cd9f4c1af215ea224a46498654079a.2592000.1727493368.282335-112092078";



    public String callErnieBotAPI(String userInput) {
        try {
            RestTemplate restTemplate = new RestTemplate();

            // 设置请求头
            HttpHeaders headers = new HttpHeaders();
            headers.set("Content-Type", "application/json");

            // 构建消息列表
            List<Map<String, String>> messages = new ArrayList<>();

            // 添加用户的消息
            Map<String, String> userMessage = new HashMap<>();
            userMessage.put("role", "user");
            userMessage.put("content", userInput);
            messages.add(userMessage);

            // 创建请求体
            String requestJson = "{\"messages\": " + new ObjectMapper().writeValueAsString(messages) + "}";

            HttpEntity<String> entity = new HttpEntity<>(requestJson, headers);

            // 调用 API
            String urlWithToken = API_URL + "?access_token=" + ACCESS_TOKEN;
            ResponseEntity<String> response = restTemplate.exchange(urlWithToken, HttpMethod.POST, entity, String.class);

            // 打印 API 返回的原始响应
            String responseBody = response.getBody();
            System.out.println("API Response: " + responseBody);

            // 解析响应
            return parseApiResponse(responseBody);
        } catch (Exception e) {
            e.printStackTrace();
            return "系统暂时无法处理您的请求，请稍后再试。";
        }
    }

    private String parseApiResponse(String apiResponse) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            Map<String, Object> map = objectMapper.readValue(apiResponse, HashMap.class);

            // 检查是否有错误信息
            if (map.containsKey("error_code") && (Integer) map.get("error_code") != 0) {
                return "API返回错误: " + map.get("error_msg");
            }

            // 提取结果内容
            return map.get("result").toString();
        } catch (Exception e) {
            e.printStackTrace();
            return "无法解析响应内容";
        }
    }

}

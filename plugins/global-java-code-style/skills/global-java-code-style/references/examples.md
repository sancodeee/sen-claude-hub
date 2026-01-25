# 代码规范示例

本文档提供代码规范的实际示例，作为 SKILL.md 的补充参考。

## 1. 命名约定示例

```java
// 类名 - 大驼峰
public class UserService { }
public interface Serializable { }

// 方法名 - 小驼峰
public void calculateTotal() { }
public String getUserName() { }

// 变量名 - 小驼峰
private int maxCount;
private String userEmail;

// 常量 - 全大写下划线
public static final int MAX_RETRY_COUNT = 3;
public static final String DEFAULT_TIMEOUT = "30s";

// 包名 - 全小写
package com.example.project.service;
```

## 2. 代码格式示例

### K&R 大括号风格

```java
// if-else
if (condition) {
    // 语句
} else if (anotherCondition) {
    // 语句
} else {
    // 语句
}

// for 循环
for (int i = 0; i < max; i++) {
    // 语句
}

// while 循环
while (condition) {
    // 语句
}

// try-catch-finally
try {
    // 可能抛出异常的代码
} catch (IllegalArgumentException e) {
    // 处理异常
} finally {
    // 清理资源
}
```

### 空格使用

```java
// 关键字后的空格
if (isValid) { }
for (int i = 0; i < 10; i++) { }
while (running) { }

// 运算符两侧的空格
int result = a + b;
boolean check = x > y && z < w;

// 逗号后的空格
method(a, b, c);
int[] arr = {1, 2, 3};
```

### 类成员组织

```java
public class Example {
    // 1. 常量
    public static final int CONSTANT = 100;

    // 2. 静态字段
    private static int staticField;

    // 3. 实例字段
    private String instanceField;


    // 4. 构造方法
    public Example() {
    }

    // 5. 静态方法
    public static void staticMethod() {
    }

    // 6. 实例方法（重载方法放在一起）
    public void process(String input) {
    }

    public void process(String input, int count) {
    }

    // 7. getter/setter
    public String getInstanceField() {
        return instanceField;
    }
}
```

## 3. Javadoc 注释示例

```java
/**
 * 用户服务类，负责用户相关的业务逻辑处理。
 *
 * <p>主要功能包括用户注册、登录、信息查询等。
 *
 * @author 张三
 * @version 1.0
 * @since 2024-01-01
 */
public class UserService {

    /**
     * 默认构造方法。
     */
    public UserService() {
    }

    /**
     * 根据用户 ID 查询用户信息。
     *
     * @param userId 用户 ID，不能为 null
     * @return 用户对象，如果不存在返回 null
     * @throws IllegalArgumentException 如果 userId 为 null 或小于等于 0
     */
    public User findById(Long userId) {
        if (userId == null || userId <= 0) {
            throw new IllegalArgumentException("userId 不能为 null 或小于等于 0");
        }
        // 实现逻辑
        return null;
    }

    /**
     * 验证用户登录凭证。
     *
     * @param username 用户名
     * @param password 密码
     * @return 验证成功返回 true，否则返回 false
     */
    public boolean authenticate(String username, String password) {
        // 实现逻辑
        return false;
    }
}
```

## 4. 异常处理示例

### 正确的异常抛出

```java
// 快速失败 - 在方法开始时检查
public void processAmount(BigDecimal amount) {
    Objects.requireNonNull(amount, "amount 不能为 null");

    if (amount.compareTo(BigDecimal.ZERO) < 0) {
        throw new IllegalArgumentException("金额不能为负数");
    }

    // 业务逻辑
}

// 抛出具体异常类型
public void readFile(String path) throws IOException {
    if (path == null || path.trim().isEmpty()) {
        throw new IllegalArgumentException("文件路径不能为空");
    }

    File file = new File(path);
    if (!file.exists()) {
        throw new FileNotFoundException("文件不存在: " + path);
    }

    // 读取逻辑
}
```

### 正确的异常捕获和日志记录

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PaymentService {
    private static final Logger logger = LoggerFactory.getLogger(PaymentService.class);

    /**
     * 处理支付。
     *
     * @param request 支付请求
     * @return 支付结果
     * @throws PaymentException 支付失败时抛出
     */
    public PaymentResult processPayment(PaymentRequest request) throws PaymentException {
        try {
            // 支付处理逻辑
            return doProcess(request);
        } catch (InsufficientBalanceException e) {
            logger.warn("支付失败: 账户余额不足, userId={}, amount={}",
                request.getUserId(), request.getAmount());
            throw new PaymentException("账户余额不足", e);
        } catch (PaymentGatewayException e) {
            logger.error("支付网关错误: userId={}, amount={}, error={}",
                request.getUserId(), request.getAmount(), e.getMessage(), e);
            throw new PaymentException("支付服务暂时不可用，请稍后重试", e);
        }
    }
}
```

### 使用 try-with-resources

```java
// 正确的资源管理
public String readFileContent(String path) throws IOException {
    StringBuilder content = new StringBuilder();

    // try-with-resources 自动关闭资源
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        String line;
        while ((line = reader.readLine()) != null) {
            content.append(line).append("\n");
        }
    }

    return content.toString();
}

// 多资源管理
public void copyFile(String source, String target) throws IOException {
    try (InputStream in = new FileInputStream(source);
         OutputStream out = new FileOutputStream(target)) {

        byte[] buffer = new byte[4096];
        int bytesRead;
        while ((bytesRead = in.read(buffer)) != -1) {
            out.write(buffer, 0, bytesRead);
        }
    }
}
```

## 5. 空值处理示例

### 使用 Optional

```java
import java.util.Optional;

public class UserRepository {

    /**
     * 根据邮箱查找用户。
     *
     * @param email 用户邮箱
     * @return Optional 包含用户对象，如果不存在返回空 Optional
     */
    public Optional<User> findByEmail(String email) {
        Objects.requireNonNull(email, "email 不能为 null");

        User user = database.queryByEmail(email);
        return Optional.ofNullable(user);
    }

    /**
     * 获取用户显示名称。
     *
     * @param email 用户邮箱
     * @return 显示名称，如果用户不存在返回 "未知用户"
     */
    public String getDisplayName(String email) {
        return findByEmail(email)
            .map(User::getNickname)
            .orElse("未知用户");
    }
}
```

### 参数校验

```java
import java.util.Objects;

public class UserService {

    public void updateUser(Long userId, String name, String email) {
        // 参数校验
        Objects.requireNonNull(userId, "userId 不能为 null");
        Objects.requireNonNull(name, "name 不能为 null");

        if (userId <= 0) {
            throw new IllegalArgumentException("userId 必须大于 0");
        }

        if (name.trim().isEmpty()) {
            throw new IllegalArgumentException("name 不能为空字符串");
        }

        // 业务逻辑
    }
}
```

## 6. 测试规范示例

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@DisplayName("UserService 单元测试")
class UserServiceTest {

    private UserService userService;
    private UserRepository mockRepository;

    @BeforeEach
    void setUp() {
        mockRepository = mock(UserRepository.class);
        userService = new UserService(mockRepository);
    }

    @Test
    @DisplayName("给定有效用户ID，当查询用户时，返回正确的用户对象")
    void givenValidUserId_whenFindById_thenReturnUser() {
        // Given
        Long userId = 1L;
        User expectedUser = new User(userId, "张三");
        when(mockRepository.findById(userId)).thenReturn(Optional.of(expectedUser));

        // When
        User actualUser = userService.getUserById(userId);

        // Then
        assertNotNull(actualUser);
        assertEquals("张三", actualUser.getName());
        verify(mockRepository).findById(userId);
    }

    @Test
    @DisplayName("给定无效用户ID，当查询用户时，抛出异常")
    void givenInvalidUserId_whenFindById_thenThrowException() {
        // Given
        Long userId = -1L;

        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            userService.getUserById(userId);
        });
    }

    @Test
    @DisplayName("给定用户不存在，当查询用户时，返回null")
    void givenNonExistentUserId_whenFindById_thenReturnNull() {
        // Given
        Long userId = 999L;
        when(mockRepository.findById(userId)).thenReturn(Optional.empty());

        // When
        User result = userService.getUserById(userId);

        // Then
        assertNull(result);
    }
}
```

## 7. 线程安全示例

### 不可变类（天然线程安全）

```java
/**
 * 不可变配置类，线程安全。
 */
public final class ImmutableConfig {
    private final String host;
    private final int port;
    private final boolean enabled;

    public ImmutableConfig(String host, int port, boolean enabled) {
        this.host = Objects.requireNonNull(host, "host 不能为 null");
        this.port = port;
        this.enabled = enabled;
    }

    public String getHost() {
        return host;
    }

    public int getPort() {
        return port;
    }

    public boolean isEnabled() {
        return enabled;
    }

    // 不提供 setter 方法
}
```

### 线程安全的计数器

```java
import java.util.concurrent.atomic.AtomicLong;

/**
 * 线程安全的计数器。
 */
public class Counter {
    private final AtomicLong count = new AtomicLong(0);

    /**
     * 增加计数。
     *
     * @return 增加后的值
     */
    public long increment() {
        return count.incrementAndGet();
    }

    /**
     * 获取当前计数。
     *
     * @return 当前值
     */
    public long get() {
        return count.get();
    }
}
```

### 使用 synchronized 的示例

```java
/**
 * 简单的线程安全缓存。
 */
public class SimpleCache<K, V> {
    private final Map<K, V> cache = new HashMap<>();

    /**
     * 获取缓存值。
     */
    public synchronized V get(K key) {
        return cache.get(key);
    }

    /**
     * 放入缓存。
     */
    public synchronized void put(K key, V value) {
        cache.put(key, value);
    }

    /**
     * 清空缓存。
     */
    public synchronized void clear() {
        cache.clear();
    }
}
```

## 8. Maven 依赖管理示例

### 在父 POM 中使用 BOM

```xml
<!-- 父 POM -->
<dependencyManagement>
    <dependencies>
        <!-- Spring Boot BOM -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.2.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>

        <!-- 其他统一版本的依赖 -->
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>3.14.0</version>
        </dependency>
    </dependencies>
</dependencyManagement>
```

### 在子模块中引入依赖（无需指定版本）

```xml
<!-- 子模块 POM -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <!-- 版本由父 POM 的 dependencyManagement 统一管理 -->
    </dependency>

    <dependency>
        <groupId>org.apache.commons</groupId>
        <artifactId>commons-lang3</artifactId>
        <!-- 版本由父 POM 的 dependencyManagement 统一管理 -->
    </dependency>
</dependencies>
```

## 9. 输入验证示例

```java
import java.util.regex.Pattern;

/**
 * 邮箱验证工具类。
 */
public class EmailValidator {

    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[A-Za-z0-9+_.-]+@(.+)$");

    /**
     * 验证邮箱格式。
     *
     * @param email 待验证的邮箱地址
     * @return 验证通过返回 true，否则返回 false
     */
    public static boolean isValid(String email) {
        if (email == null || email.trim().isEmpty()) {
            return false;
        }

        // 防止 ReDoS 攻击：限制邮箱长度
        if (email.length() > 254) {
            return false;
        }

        return EMAIL_PATTERN.matcher(email).matches();
    }
}
```

### SQL 注入防护

```java
// 使用 PreparedStatement 防止 SQL 注入
public User findByUsername(String username) {
    String sql = "SELECT * FROM users WHERE username = ?";

    try (Connection conn = dataSource.getConnection();
         PreparedStatement stmt = conn.prepareStatement(sql)) {

        stmt.setString(1, username);
        ResultSet rs = stmt.executeQuery();

        if (rs.next()) {
            return mapToUser(rs);
        }

        return null;
    } catch (SQLException e) {
        logger.error("查询用户失败: username={}", username, e);
        throw new DataAccessException("查询用户失败", e);
    }
}

// 错误示例：字符串拼接（容易受 SQL 注入攻击）
// 不要这样做！
// String sql = "SELECT * FROM users WHERE username = '" + username + "'";
```
